# 0005 — Ad blocking: local Blocky resolver + nftables redirect + uBlock Origin

Status: proposed (2026-10-16)

**Context.** Ads should be blocked for as many apps as possible on every network without any action from the user, and the
whole setup must rebuild unattended from the repo.

**Decision.** Blocky on 127.0.0.1:53 with OISD big + HaGeZi Pro lists and DoT upstreams, its one
YAML config in git; nftables redirects all port-53 traffic to it, drops DoT, and drops DoH to a list of well-known IPv4 resolvers;
NetworkManager runs with dns=none and a static resolv.conf; Firefox has DoH off and locked by policy
and uBlock Origin force-installed; yt-dlp + mpv for video; the hotspot interface inherits all of it.

**Alternatives.** AdGuard Home (adds a web UI; first run is a wizard and the config schema changes
between versions, so it is harder to provision blind). Pi-hole v6 (heavier). Browser-only blocking
(misses every other app). All resolvers fit the same slot behind the firewall, so this is cheap to revisit.

**Consequences.** Some sites and apps break and need entries in custom-allow.txt; the acceptance
tests in docs/04 gate the stage; no UI on the device for the resolver until Pocket TUI gets a tab for it.
