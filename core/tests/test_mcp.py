"""The MCP server: tool registry and calls in-process, plus one real stdio handshake."""
import asyncio
import json
import os
import sys

import pytest

from pocket_core import mcp_server

TOOLS = {"device_status", "power_status", "net_status", "snapshot_list", "snapshot_create", "resolver_status",
         "resolver_set", "kb_search", "audit_tail", "set_power_profile", "set_brightness"}


def payload(result):
    """Tool result -> Python object, for both the mcp 1.x and 2.x result shapes."""
    if isinstance(result, tuple):  # mcp 1.x in-process call_tool: (content blocks, structured dict)
        blocks, structured = result
    else:  # CallToolResult: 2.x snake_case, 1.x camelCase
        blocks = result.content
        structured = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and structured:
        return structured["result"] if set(structured) == {"result"} else structured
    return json.loads(blocks[0].text)


@pytest.fixture(autouse=True)
def fake_backend(monkeypatch):
    monkeypatch.setenv("POCKET_BACKEND", "fake")
    monkeypatch.setattr(mcp_server, "_backend", None)


def test_tools_and_resource_in_process():
    async def go():
        s = mcp_server.server
        tools = await s.list_tools()
        assert {t.name for t in tools} == TOOLS and all(t.description for t in tools)
        assert payload(await s.call_tool("device_status", {}))["temp_c"] == 48.2
        r = payload(await s.call_tool("set_brightness", {"pct": 33}))
        assert r["pct"] == 33 and r["ok"]
        assert payload(await s.call_tool("set_power_profile", {"name": "endurance"}))["ok"]
        assert payload(await s.call_tool("power_status", {}))["profile"] == "endurance"
        assert len(payload(await s.call_tool("kb_search", {"query": "first aid", "limit": 2}))) == 2
        assert len(payload(await s.call_tool("audit_tail", {"n": 4}))) == 4
        assert payload(await s.call_tool("snapshot_create", {"label": "mcp"}))["ok"]
        assert [str(r.uri) for r in await s.list_resources()] == ["pocket://status"]
        text = [c.content for c in await s.read_resource("pocket://status")][0]
        assert "Raspberry Pi 5" in text and "ExampleNet" in text and "profile endurance" in text

    asyncio.run(go())


def test_stdio_handshake():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def go():
        params = StdioServerParameters(command=sys.executable, args=["-m", "pocket_core.mcp_server"],
                                       env={**os.environ, "POCKET_BACKEND": "fake"})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                assert {t.name for t in (await session.list_tools()).tools} == TOOLS
                assert payload(await session.call_tool("set_brightness", {"pct": 20}))["pct"] == 20
                res = await session.read_resource("pocket://status")
                assert "Raspberry Pi 5" in res.contents[0].text

    asyncio.run(asyncio.wait_for(go(), 90))
