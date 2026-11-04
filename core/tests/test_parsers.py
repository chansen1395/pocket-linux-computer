"""Pure parser tests: no network, no Pi."""
from pocket_core import parsers as P

PMIC = """\
 3V7_WL_SW_A current(0)=0.00000000A
 3V3_SYS_A current(1)=0.02197000A
 1V8_SYS_A current(2)=0.19946000A
 VDD_CORE_A current(7)=1.08691000A
 HDMI_A current(11)=0.02197000A
 3V7_WL_SW_V volt(15)=3.74145000V
 3V3_SYS_V volt(16)=3.30805000V
 1V8_SYS_V volt(17)=1.80218000V
 VDD_CORE_V volt(22)=0.72532000V
 HDMI_V volt(26)=5.09851000V
 EXT5V_V volt(27)=5.09851000V
 BATT_V volt(28)=0.00000000V
"""

KIWIX_HTML = """<!DOCTYPE html><html><head><title>Search: raspberry</title></head><body>
<div class="header"><a href="/">home</a></div>
<div class="results">
  <ul>
    <li>
      <a href="/content/wikipedia_en_all_maxi_2024-01/A/Raspberry_Pi">
        Raspberry Pi
      </a>
      <cite>The <b>Raspberry</b> Pi is a series of small single-board computers...</cite>
      <div class="book-title">from Wikipedia</div>
      <div class="informations">7,321 words</div>
    </li>
    <li>
      <a href="/content/wikipedia_en_all_maxi_2024-01/A/Raspberry_Pi_OS">Raspberry Pi OS</a>
      <cite>Raspberry Pi OS is a Unix-like operating system based on <b>Debian</b>.</cite>
      <div class="book-title">from Wikipedia</div>
    </li>
  </ul>
</div>
<div class="footer"><a href="/search?pattern=raspberry&start=25">next</a></div>
</body></html>"""


def test_throttled_decode():
    assert P.parse_throttled("throttled=0x0") == ("0x0", [])
    hexv, flags = P.parse_throttled("throttled=0x50005\n")
    assert hexv == "0x50005"
    assert flags == ["under-voltage now", "throttled now", "under-voltage occurred", "throttled occurred"]


def test_pmic_parse():
    rails, watts = P.parse_pmic(PMIC)
    assert len(rails) == 12 and rails["VDD_CORE_A"] == 1.0869 and rails["EXT5V_V"] == 5.0985
    expected = 0.02197 * 3.30805 + 0.19946 * 1.80218 + 1.08691 * 0.72532 + 0.02197 * 5.09851  # + 0 * 3.74145
    assert watts == round(expected, 2) == 1.33
    assert P.parse_pmic("") == ({}, None)
    assert P.parse_pmic("EXT5V_V volt(27)=5.09851000V\n") == ({"EXT5V_V": 5.0985}, None)


def test_kiwix_parse():
    res = P.parse_kiwix(KIWIX_HTML, "http://127.0.0.1:8090")
    assert [r["title"] for r in res] == ["Raspberry Pi", "Raspberry Pi OS"]
    assert res[0]["url"] == "http://127.0.0.1:8090/content/wikipedia_en_all_maxi_2024-01/A/Raspberry_Pi"
    assert res[0]["snippet"] == "The Raspberry Pi is a series of small single-board computers..."
    assert res[1]["snippet"].endswith("based on Debian.")
    assert P.parse_kiwix("<html><body><h1>Error</h1><p>No book found</p></body></html>") == []


def test_dns_query_packet():
    pkt = P.dns_build_query("debian.org", 0xBEEF)
    assert pkt[:12] == b"\xbe\xef\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    assert pkt[12:] == b"\x06debian\x03org\x00\x00\x01\x00\x01"


def test_dns_parse_response():
    question = P.dns_build_query("debian.org", 7)[12:]
    header = b"\x00\x07\x81\x80\x00\x01\x00\x03\x00\x00\x00\x00"  # id 7, response+RD+RA, 1 question, 3 answers
    cname = b"\xc0\x0c\x00\x05\x00\x01\x00\x00\x0e\x10\x00\x02\xc0\x0c"  # CNAME with a compressed rdata name
    a_rr = b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x0e\x10\x00\x04"  # name pointer, type A, IN, ttl 3600, rdlen 4
    data = header + question + cname + a_rr + bytes([151, 101, 2, 132]) + a_rr + bytes([151, 101, 130, 132])
    assert P.dns_parse_response(data) == {"id": 7, "rcode": 0, "answers": ["151.101.2.132", "151.101.130.132"]}
    servfail = P.dns_parse_response(b"\x00\x07\x81\x82\x00\x01\x00\x00\x00\x00\x00\x00" + question)
    assert servfail["rcode"] == 2 and servfail["answers"] == []


def test_net_parsers():
    assert P.parse_nmcli_wifi("no:Other:40\nyes:Example\\:Net:71\n") == {"ssid": "Example:Net", "signal": 71}
    assert P.parse_nmcli_wifi("no:Other:40\n") is None
    addr = ('[{"ifname":"lo","operstate":"UNKNOWN","addr_info":[{"family":"inet","local":"127.0.0.1"}]},'
            '{"ifname":"wlan0","operstate":"UP","addr_info":[{"family":"inet6","local":"fe80::1"},'
            '{"family":"inet","local":"192.0.2.42"}]},{"ifname":"eth0","operstate":"DOWN","addr_info":[]}]')
    assert P.parse_ip_addr(addr) == [{"name": "wlan0", "ip": "192.0.2.42", "state": "up"},
                                     {"name": "eth0", "ip": None, "state": "down"}]
    assert P.parse_default_route('[{"dst":"default","gateway":"192.0.2.1","dev":"wlan0"}]') == "wlan0"
    assert P.parse_default_route("[]") is None
    assert P.parse_meminfo("MemTotal:        4142340 kB\nMemFree:  100 kB\nMemAvailable:    2201600 kB\n") == (4045, 2150)
