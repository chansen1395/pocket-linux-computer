#!/usr/bin/env bash
# Run the provisioning stages inside an arm64 Debian 13 container that mimics Raspberry Pi OS.
# Proves package names, downloads, config installs and script logic; cannot prove anything that
# needs real hardware or a live systemd (EEPROM, PCIe, service start-up, firewall loading).
#
#   provision/test/container-test.sh            # dry run of everything, then real run of 10 20 30 50 55 60 70
#   provision/test/container-test.sh 30 50      # real run of chosen stages only
#
# The container is started detached (QEMU is slow); follow it with: docker logs -f pocket-test
set -euo pipefail
cd "$(dirname "$0")/../.."
stages="${*:-10 20 30 50 55 60 70}"
src="$(pwd -W 2>/dev/null || pwd)"      # Windows path under Git Bash, POSIX path elsewhere

docker build --platform linux/arm64 -t pocket-test provision/test
docker rm -f pocket-test >/dev/null 2>&1 || true
MSYS_NO_PATHCONV=1 docker run -d --name pocket-test --platform linux/arm64 --cap-add NET_ADMIN \
  -v "$src:/src:ro" pocket-test bash -c "
set -e
mkdir -p /home/tester/pocket && tar -C /src --exclude=.git --exclude=.venv --exclude=__pycache__ --exclude=.pytest_cache --exclude='*.egg-info' -cf - . | tar -C /home/tester/pocket -xf -
chown -R tester:tester /home/tester/pocket && cd /home/tester/pocket/provision
chmod +x run.sh stages/*.sh
echo '=== DRY RUN all ==='
DRY_RUN=1 SUDO_USER=tester ./run.sh all
echo '=== REAL: $stages ==='
SUDO_USER=tester POCKET_MANIFEST=/home/tester/pocket/provision/test/manifest-tiny.txt ./run.sh $stages
echo '=== CHECKS ==='
/usr/local/bin/blocky version && echo 'blocky: ok'
nft -c -f /etc/nftables.conf && echo 'nftables.conf: parses'
sudo -u tester -H bash -lc 'claude --version' && echo 'claude: ok'
ls -l /usr/local/bin/pocket-* /etc/blocky/config.yml /etc/sudoers.d/pocket-helper /home/tester/.claude/settings.json
ls /data/kiwix || true
./run.sh --list
echo '=== TEST COMPLETE ==='
"
echo "started container pocket-test; follow with: docker logs -f pocket-test"
