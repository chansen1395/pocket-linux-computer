# arm64 Debian 13 image that mimics Raspberry Pi OS Trixie closely enough to exercise the
# provisioning stages without hardware: the Raspberry Pi apt repo, sudo, a `tester` user with
# passwordless sudo, an SSH key, a fake /boot/firmware/config.txt, and no running systemd
# (SYSTEMCTL_OFFLINE=1 makes `systemctl enable` work as symlinks only).
FROM --platform=linux/arm64 debian:trixie
ENV DEBIAN_FRONTEND=noninteractive SYSTEMCTL_OFFLINE=1 POCKET_SKIP_HW_CHECK=1 POCKET_USER=tester
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg sudo systemd procps iproute2 util-linux \
 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://archive.raspberrypi.com/debian/raspberrypi.gpg.key | gpg --dearmor -o /usr/share/keyrings/raspberrypi-archive-keyring.gpg \
 && echo "deb [trusted=yes signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.gpg] https://archive.raspberrypi.com/debian/ trixie main" > /etc/apt/sources.list.d/raspi.list
# trusted=yes: Debian 13's sqv rejects the archive key's old binding signature; the real Pi OS image
# ships raspberrypi-archive-keyring, so this only affects the test container.
RUN useradd -m -s /bin/bash -G sudo tester \
 && echo 'tester ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/tester && chmod 0440 /etc/sudoers.d/tester \
 && mkdir -p /boot/firmware && printf '# fake config.txt for container tests\n[all]\n' > /boot/firmware/config.txt \
 && mkdir -p /home/tester/.ssh && echo 'ssh-ed25519 AAAATESTKEYONLY test@container' > /home/tester/.ssh/authorized_keys \
 && chown -R tester:tester /home/tester && chmod 700 /home/tester/.ssh
WORKDIR /home/tester
CMD ["bash"]
