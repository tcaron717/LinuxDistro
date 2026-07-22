#version=F44
lang en_US.UTF-8
keyboard us
timezone UTC --utc
network --bootproto=dhcp --device=link --activate --onboot=on
rootpw --lock
firewall --enabled --service=ssh
selinux --enforcing
services --enabled=sshd,NetworkManager
bootloader --location=mbr --timeout=1
zerombr
clearpart --all --initlabel
reqpart
part / --fstype="ext4" --size=16384 --grow
reboot

# Core Fedora repos. DNF expands $releasever and $basearch for the build host.
url --url="https://download.fedoraproject.org/pub/fedora/linux/releases/$releasever/Everything/$basearch/os/"
repo --name=fedora --baseurl="https://download.fedoraproject.org/pub/fedora/linux/releases/$releasever/Everything/$basearch/os/"
repo --name=updates --baseurl="https://download.fedoraproject.org/pub/fedora/linux/updates/$releasever/Everything/$basearch/"

# The local `aifirst-ai` repository is injected by scripts/build-iso.sh.
# LOCAL_AIFIRST_REPO

%packages
@workstation-product-environment

# BEGIN_MANAGED_PACKAGES
# Synced from manifests via scripts/sync-kickstart-packages.sh
NetworkManager-tui
aifirst-ai
ansible
cargo
cmake
curl
distrobox
dnf-automatic
dracut-live
fedora-workstation-repositories
flatpak
gcc
gcc-c++
git
git-lfs
gnome-terminal
golang
htop
jq
libstdc++-devel
make
nodejs
npm
openssh-clients
pipx
podman
python3
python3-devel
python3-pip
python3-pydantic
python3-requests
python3-rich
python3-tkinter
python3-virtualenv
rsync
rust
shellcheck
tmux
vim-enhanced
wget
zsh
# END_MANAGED_PACKAGES
%end

%post --log=/root/ks-post.log
set -euxo pipefail

# Enable faster first-time updates and unattended security updates.
systemctl enable dnf-automatic.timer || true

# Prepare directories for optional AI runtime installers.
mkdir -p /opt/ai-first/bin /opt/ai-first/config

# Optional assistant payload hook:
# If your compose process injects assistant files into /run/install/repo/aifirst,
# install and enable them automatically.
if [[ -x /run/install/repo/aifirst/scripts/install-assistant.sh ]]; then
  /run/install/repo/aifirst/scripts/install-assistant.sh || true
fi

# Placeholder assistant hook.
cat >/opt/ai-first/bin/assistant-bootstrap.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "Implement distro assistant bootstrap here."
EOF
chmod +x /opt/ai-first/bin/assistant-bootstrap.sh
%end
