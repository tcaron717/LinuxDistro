# AI-First Fedora Spin Starter

This repository scaffolds a Fedora-based Linux spin focused on AI tooling and an assistant-first UX.

## What this gives you

- A Kickstart baseline for an installable desktop image
- Manifest-driven package lists for base and AI workloads
- Scripts to build an ISO, validate config, and create a local RPM repo
- Roadmap docs for turning a prototype into a maintainable distro

## Repository layout

- `kickstarts/ai-first-fedora.ks`: Main Kickstart file
- `manifests/base-packages.txt`: Baseline package list
- `manifests/ai-packages.txt`: AI/dev tooling package list
- `scripts/sync-kickstart-packages.sh`: Sync manifest packages into Kickstart
- `scripts/build-iso.sh`: Build Fedora 44 ISO with `livemedia-creator` for `x86_64` or `aarch64`
- `scripts/create-local-repo.sh`: Build local RPM metadata
- `scripts/validate-kickstart.sh`: Validate Kickstart syntax and required tools
- `assistant/assistantd.py`: Local assistant daemon over Unix socket
- `assistant/assistant_cli.py`: CLI client for assistant actions
- `assistant/assistant_gui.py`: Desktop GUI launcher and settings manager
- `configs/assistant-policy.json`: Allowlisted action policy
- `desktop/assistant-gui.desktop`: Desktop menu launcher entry
- `docs/tai-assistant-mock-layout-spec.md`: Mock screenshot/wireframe layout spec
- `scripts/install-assistant.sh`: Install assistant and systemd unit
- `tools/aifirst-ai/`: Source for packaged AI CLI (`aifirst-ai`)
- `packaging/rpm/aifirst-ai.spec`: RPM spec for `aifirst-ai`
- `scripts/build-aifirst-ai-rpm.sh`: Build custom RPM in `out/rpmbuild`
- `docs/roadmap.md`: Suggested milestones

## Prerequisites (Fedora build host)

Install required tools:

```bash
sudo dnf install -y \
  pykickstart lorax-lmc-novirt livemedia-creator \
  qemu-img qemu-system-x86 xorriso createrepo_c
```

## Quick start

1. Sync package manifests into Kickstart:

```bash
./scripts/sync-kickstart-packages.sh
```

2. Validate Kickstart:

```bash
./scripts/validate-kickstart.sh
```

3. Build ISO (requires sudo/root). Build each architecture on a matching Fedora
   build host; `livemedia-creator` does not cross-build these images:

```bash
make build-iso ARCH=x86_64
make build-iso ARCH=aarch64
```

The default architecture is the build host architecture. Outputs are written to
`out/iso/x86_64/` and `out/iso/aarch64/` respectively.

The build runs Anaconda with `--no-virt`; use a dedicated Fedora VM, not a
workstation containing data you need to protect.

## Assistant quick start

Run daemon in development mode:

```bash
make run-assistant-dev
```

Run desktop GUI locally:

```bash
make run-assistant-gui-dev
```

In another shell:

```bash
python3 ./assistant/assistant_cli.py disk_usage_summary --socket-path ./out/assistantd.sock
python3 ./assistant/assistant_cli.py install_package --package htop --approve --dry-run --socket-path ./out/assistantd.sock
python3 ./assistant/assistant_cli.py settings init
python3 ./assistant/assistant_cli.py settings add --name openai-prod --provider openai_compatible --model gpt-4o-mini --api-key-env OPENAI_API_KEY
python3 ./assistant/assistant_cli.py settings set-default --name openai-prod
python3 ./assistant/assistant_cli.py settings set-permissions --mode full_access
python3 ./assistant/assistant_cli.py ai_query --mode ask --profile openai-prod --prompt "How do I check GPU info?" --socket-path ./out/assistantd.sock
```

For systemd deployments, edit the daemon config file path (`/etc/aifirst/aifirst-ai.json`) so settings affect `assistantd`:

```bash
sudo assistant-cli settings set-permissions --settings-path /etc/aifirst/aifirst-ai.json --mode full_access
sudo assistant-cli settings add --settings-path /etc/aifirst/aifirst-ai.json --name openai-prod --provider openai_compatible --model gpt-4o-mini --api-key-env OPENAI_API_KEY
```

Run core logic tests:

```bash
make test-assistant-core
```

Install as a system service on Fedora:

```bash
make install-assistant
sudo systemctl start assistantd
```

Then launch the desktop app:

```bash
assistant-gui
```

## Local RPM repo for your custom packages

Place RPM files in `out/repo/` and run:

```bash
./scripts/create-local-repo.sh out/repo
```

Then add the repo URL/path in `kickstarts/ai-first-fedora.ks`.

Build the included `aifirst-ai` RPM:

```bash
make build-aifirst-ai-rpm
```

Copy generated RPMs into `out/repo/`, run `make create-repo REPO=out/repo`, then rebuild your ISO.
The ISO build script automatically adds this repository for `aifirst-ai`; no
manual Kickstart edit is needed.

## Next recommended step

Build your first alpha with stock Fedora + your curated AI toolchain, then iterate on assistant integration and UX automation.
