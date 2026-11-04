# Runbook 10 — First contact: the Pi is on Wi-Fi, now what

Preconditions: the card was flashed with the kit (runbook 00), the Pi booted from its own power
supply, 3 minutes have passed. Run it from the PC, by hand or with Claude Code driving.

## 1. Find it

```powershell
ping pocket.local -n 1                                   # mDNS; or:
powershell -File tools\find-pocket.ps1                   # ping sweep for Raspberry Pi MAC prefixes
ssh -o StrictHostKeyChecking=accept-new <user>@pocket.local   # the user and key from your user-data
```

## 2. Check the first boot

```bash
cloud-init status --long                 # done, no errors
sudo tail -n 40 /var/log/pocket-firstboot.log   # stage 10 output; the last line is "stage 10 exit N" (written by user-data.example)
sudo ./pocket/provision/run.sh --list    # from ~; 10-base should show a completion time
vcgencmd get_throttled                  # 0x0 on a good supply; 0x50005-ish on a PC port
```

SSH is key-only, and stage 10 leaves sshd off when the account has no `~/.ssh/authorized_keys`. If SSH is
refused, check that your public key is in `user-data`, or log in on the console and add it.

If stage 10 did not finish: `cd ~/pocket/provision && sudo ./run.sh 10` (idempotent).

## 3. Remaining stages, one at a time, watching for lock-outs

Never copy new scripts onto the Pi while a stage is running: bash reads scripts incrementally, and
overwriting a running one corrupts the run. Sync, then run.

```bash
cd ~/pocket/provision
sudo ./run.sh 30            # resolver + firewall; keep the SSH session open, open a second one to verify
sudo ./run.sh 30 -- --test  # five acceptance checks
sudo ./run.sh 50            # Claude Code + hooks (sign-in is interactive: run `claude` afterwards)
sudo ./run.sh 55            # pocketctl, MCP server, Pocket TUI (after 50: needs claude on PATH)
sudo ./run.sh 60            # restic + syncthing (fill /etc/pocket/restic.env first; the timer skips until then)
sudo ./run.sh 70            # kiwix + the manifest downloads (GBs; only on a fast link)
sudo ./run.sh 40            # desktop apps; only once a display is attached or a VNC session is wanted
```

Interactive step for you: run `claude` once and sign in with your Claude subscription.

## 4. Measure (feeds the decisions in docs/decisions/)

```bash
pocketctl status                           # temps, rails, watts (PMIC estimate)
vcgencmd pmic_read_adc | grep -E 'EXT5V|VDD_CORE'
sudo apt install -y stress-ng && stress-ng --cpu 4 --timeout 120 & watch -n5 'vcgencmd measure_temp; vcgencmd get_throttled'
dd if=/dev/zero of=/data/ddtest bs=1M count=1024 conv=fsync; rm /data/ddtest   # SD write speed
free -m; systemd-analyze                                                         # RAM at rest, boot time
```

Record results in docs/01-hardware.md §5 and move decisions 0001/0004 toward *accepted* or supersede them.

## 5. Rollback

Everything stage-level is re-runnable; the firewall allows SSH on 22 from anywhere; if DNS breaks,
`sudo systemctl stop blocky nftables` and `echo nameserver 9.9.9.9 | sudo tee /etc/resolv.conf`
restores a plain resolver until the stage is fixed.
