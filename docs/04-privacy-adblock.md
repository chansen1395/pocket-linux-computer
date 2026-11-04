# 04 — Privacy and unilateral ad blocking

Requirement: block ads and trackers for as many applications as possible, on every network (home Wi-Fi,
phone tether, LTE, café hotspot), without the builder doing anything. A single layer cannot do that, so there
are five. The limits of each layer are stated below; nothing here is a guarantee that no ad gets through.

## Layer 1: a filtering DNS resolver on the device

**Blocky** on `127.0.0.1:53`, with the hotspot's dnsmasq forwarding to it in travel-router mode.

- Single Go binary, the whole configuration is one YAML file in `provision/config/etc/blocky/`,
  DNS-over-TLS upstreams built in, starts with no setup wizard (so a rebuild is unattended).
  A query log and a small HTTP API on `127.0.0.1:4000` for debugging.
- Blocklists: **OISD big** (low false positives) + **HaGeZi Pro** + your own allow and deny
  files. Refreshed daily.
- Upstreams: Quad9 and Cloudflare over DoT; optionally a local **Unbound** recursive resolver behind it
  (DNSSEC, no third party sees the queries at all, slower cold cache). Decided per network profile.
- Alternatives evaluated: AdGuard Home (same idea plus a web UI, but its first run is a wizard and
  its config schema moves), Pi-hole v6 (heavier). All three fit the same slot; the firewall layer
  makes them interchangeable, so swapping later costs one stage.

## Layer 2: the firewall makes the resolver unavoidable

nftables rules in `provision/config/etc/nftables.conf`:

1. Redirect every outbound UDP/TCP port 53 packet that is not from the resolver's own user to `127.0.0.1:53`
   (IPv4 and IPv6 for local processes; hotspot clients' IPv4 port 53 only).
2. Drop outbound DNS-over-TLS (port 853, IPv4 and IPv6) from any process except the resolver's own user.
   Drop DoH and QUIC (port 443) only to a fixed list of well-known **IPv4** public resolver addresses (Google,
   Cloudflare, Quad9, OpenDNS, AdGuard, ControlD). DoH to any other host, and to those resolvers over IPv6,
   is not blocked by the firewall. Firefox has DoH disabled and locked by policy, which covers the browser.
3. NetworkManager runs with `dns=none`; `/etc/resolv.conf` is a static file pointing at `127.0.0.1`,
   so a DHCP server on a hotel network cannot swap resolvers under us.
4. Rules apply on every interface, including the LTE modem and the USB tether, because they are
   written against output chains, not interface names.

## Layer 3: in the browser

- Firefox with **uBlock Origin** (handles the first-party and inline ads DNS cannot touch, and
  YouTube's player ads), strict tracking protection, no Pocket, no telemetry, no studies, no sponsored
  tiles, HTTPS-only mode. These are set by `provision/config/etc/firefox/policies/policies.json`, so the
  profile rebuilds. **arkenfox user.js** hardening is planned: no `user.js` exists in this repository yet.
- Chromium is installed only if a site demands it and lives in a separate, sandboxed profile.

## Layer 4: media without players

- YouTube through `yt-dlp` piped to `mpv` (Pocket TUI has a "Watch" box that takes a URL or a search).
- Podcasts and feeds through a local reader (`newsboat`) rather than apps with ad slots.
- Invidious or Piped instances as a browser fallback.

## Layer 5: travel router mode

When the device shares its connection (phone, laptop, a friend's device), the hotspot interface
gets the same resolver and the same firewall rules, so everything behind it is ad-free too.
The hotspot itself is set up by hand through NetworkManager for now (a `pocketctl` command for it is planned); the firewall rules for it are already in place.

## Beyond ads

- **No Chrome.** Firefox primary; Chromium quarantined.
- **No telemetry:** VSCodium instead of VS Code, Raspberry Pi OS telemetry (the `rpi-eeprom`/apt
  pings are harmless, but the stage documents what phones home and why).
- **Encryption at rest:** see `02-software.md §5` and decision 0006.
- **Wi-Fi hygiene:** random MAC per network is set in stage 30. Not auto-joining open networks and hiding the
  hotspot SSID are planned, not done.
- **Nothing listens** on the public internet except SSH (keys only) and mosh.

## Acceptance test (runs from `provision/stages/30-network.sh --test`)

1. `dig @8.8.8.8 pagead2.googlesyndication.com` from a normal shell returns `0.0.0.0` (the redirect works).
   The curated lists leave the `doubleclick.net` apex unblocked on purpose, so the test uses an unambiguous ad host.
2. `curl https://dns.google/resolve?name=example.com` fails (DoH to a listed resolver is blocked).
3. `nslookup ads.example` on the hotspot interface from a connected phone returns the sinkhole.
4. Switching from Wi-Fi to tether to LTE keeps `resolv.conf` at `127.0.0.1`.
5. A known ad-heavy page in Firefox shows zero blocked-request leaks in the uBlock logger.
