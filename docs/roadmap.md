# AI-First Fedora Spin Roadmap

## Phase 1: Working Alpha (2-4 weeks)

- Build bootable ISO from `kickstarts/ai-first-fedora.ks`
- Confirm install in VM and one physical device
- Provide curated AI/dev tools from manifests
- Add first-boot script hooks for assistant bootstrap

Exit criteria:

- ISO installs successfully end-to-end
- Basic dev stack works (`python`, `node`, `rust`, `podman`)
- System updates from Fedora repos without manual fixes

## Phase 2: Assistant Integration (4-8 weeks)

- Build a local "AI assistant service" wrapper with CLI and desktop launcher
- Add provider abstraction (local models, API-backed models)
- Add guided system tasks (updates, drivers, troubleshooting)
- Add privacy modes and model/runtime toggles

Exit criteria:

- Assistant can execute at least 5 common admin workflows safely
- Logs are inspectable and privileged actions are consent-gated

## Phase 3: Distribution Hardening

- Replace branding and release RPMs (`*-release` packages)
- Add signed package pipeline + hosted update repo
- Add CI: kickstart validation, ISO build, VM smoke tests
- Add release notes and upgrade path docs

Exit criteria:

- Reproducible builds from Git
- Signed updates and versioned releases
