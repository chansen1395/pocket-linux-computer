# pocket_core

The shared device core of the Pocket device: one `Backend` with every capability the device offers, used by
three front ends that therefore never disagree:

- `pocketctl`: the command line (`pocketctl status`, `pocketctl power endurance`, ...)
- `pocket-mcp`: an MCP server so Claude Code can call the same things as typed tools
- the Pocket TUI (separate package in `../tui`) imports `pocket_core.get_backend()`

Two backends: `LinuxBackend` reads the real Pi (sysfs, `vcgencmd`, `ip -j`, `nmcli`, btrfs, Blocky,
kiwix-serve); `FakeBackend` returns deterministic values and keeps setter state in memory, so everything runs
and tests on a laptop. `get_backend()` picks Linux on a Raspberry Pi and Fake elsewhere; `POCKET_BACKEND=fake`
(or `linux`) overrides. Nothing raises: unreadable values are `None`, failed actions return `ok: false` with a
`message`, and the CLI exits 1 on `ok: false`.

## Install on the Pi (Raspberry Pi OS Trixie, Python 3.13)

Provision stage 55 does this. By hand:

```bash
python3 -m venv ~/.venvs/pocket
~/.venvs/pocket/bin/pip install -e ~/pocket/core
mkdir -p ~/.local/bin
ln -sf ~/.venvs/pocket/bin/pocketctl ~/.venvs/pocket/bin/pocket-mcp ~/.local/bin/
pocketctl status
```

Pure Python; `mcp` (2.3 or newer; older releases fail with current pydantic) and its dependencies install as aarch64 wheels. Runtime helpers, all optional (each degrades
gracefully when missing): `vcgencmd` (user in group `video`), `iproute2`, `network-manager`, `brightnessctl`
(group `video`, stage 40), `btrfs-progs`, Blocky on `127.0.0.1:4000`, kiwix-serve on `127.0.0.1:8090`.

### Permissions for the setters

Power profile and snapshot writes need root. They go through one small program, `pocket-helper`
(`provision/config/usr/local/bin/pocket-helper`), run with `sudo -n`, and report `ok: false` when it is not
installed. Stages 50 and 55 install it root-owned in `/usr/local/bin` and write a one-line sudoers rule that
names that path and nothing else.

The helper checks every request against an exact allow-list (a fixed set of verbs, `policyN` names, governors,
profile names, a frequency range, and snapshot names of one fixed shape) before it writes or runs anything. A
sudoers rule with a wildcard, such as `tee .../policy*/scaling_governor`, cannot do this: the star matches
spaces and slashes, so it also allows `tee <that path> /etc/sudoers.d/x`. The validation is tested in
`tests/test_helper.py`.

## Register the MCP server with Claude Code

```bash
claude mcp add pocket -- pocket-mcp        # or merge claude-mcp.json into .mcp.json / ~/.claude.json
```

Eleven tools: `device_status`, `power_status`, `net_status`, `snapshot_list`, `snapshot_create(label)`,
`resolver_status`, `resolver_set(enabled)`, `kb_search(query, limit)`, `audit_tail(n)`,
`set_power_profile(name)`, `set_brightness(pct)`. Resource `pocket://status` is a one-line summary.
`resolver_set(false)` pauses Blocky for 15 minutes, then blocking comes back by itself.

## CLI

```
pocketctl status                      pocketctl snapshot list | create <label>
pocketctl power [performance|balanced|endurance]
pocketctl net                         pocketctl resolver [status|on|off]
pocketctl kb <query...> [-n N]        pocketctl audit [-n N]
pocketctl brightness <0-100>          add --json to any command for the raw dict
```

## Development on a laptop (Windows, macOS, Linux)

```bash
python -m venv core/.venv
core/.venv/Scripts/python -m pip install -e "core[dev]"      # bin/ instead of Scripts/ on POSIX
core/.venv/Scripts/python -m pytest core/tests -q            # fake backend, no network
POCKET_BACKEND=fake core/.venv/Scripts/pocketctl status --json
```

Environment overrides for a dry run against real services: `POCKET_BLOCKY_URL`, `POCKET_KIWIX_URL`,
`POCKET_SNAPSHOT_DIR`, `POCKET_PROFILE_FILE`, `POCKET_AUDIT_LOG`.

## Layout

```
pocket_core/backend.py     Backend protocol, get_backend(), snapshot naming
pocket_core/parsers.py     pure parsers: vcgencmd, /proc, ip -j, nmcli, kiwix HTML, DNS packets
pocket_core/linux.py       the Pi backend (every read wrapped; privileged writes via pocket-helper)
pocket_core/fake.py        deterministic backend with in-memory state
pocket_core/cli.py         `pocketctl` (argparse, --json everywhere, exit 1 on ok=false)
pocket_core/mcp_server.py  `pocket-mcp` (MCP server, stdio; tested with mcp 2.3)
tests/                     pytest, fake backend and helper validation only, no network
```
