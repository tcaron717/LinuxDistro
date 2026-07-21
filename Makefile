SHELL := /usr/bin/env bash

.PHONY: help sync-packages validate build-iso create-repo vm-smoke install-assistant run-assistant-dev run-assistant-gui-dev test-assistant-core build-aifirst-ai-rpm

help:
	@echo "Targets:"
	@echo "  make sync-packages            # Sync manifests into kickstart"
	@echo "  make validate                 # Validate kickstart syntax"
	@echo "  make build-iso [ARCH=...]     # Build Fedora 44 ISO for x86_64 or aarch64 (sudo required)"
	@echo "  make create-repo REPO=path    # Create/refresh local RPM repo metadata"
	@echo "  make vm-smoke [ISO=path]      # Boot ISO in QEMU"
	@echo "  make install-assistant        # Install assistantd/assistant-cli on host"
	@echo "  make run-assistant-dev        # Run assistantd in local dev mode"
	@echo "  make run-assistant-gui-dev    # Run desktop GUI locally"
	@echo "  make test-assistant-core      # Validate assistant action policy logic"
	@echo "  make build-aifirst-ai-rpm     # Build RPM for aifirst-ai tool"

sync-packages:
	./scripts/sync-kickstart-packages.sh

validate:
	./scripts/validate-kickstart.sh

build-iso: sync-packages validate
	./scripts/build-iso.sh

create-repo:
	@test -n "$(REPO)" || (echo "Set REPO=/path/to/rpms" && exit 1)
	./scripts/create-local-repo.sh "$(REPO)"

vm-smoke:
	./scripts/run-vm-smoke-test.sh "$(ISO)"

install-assistant:
	sudo ./scripts/install-assistant.sh

run-assistant-dev:
	mkdir -p ./out
	python3 ./assistant/assistantd.py --socket-path ./out/assistantd.sock --policy-path ./configs/assistant-policy.json --assistant-config-path ./configs/aifirst-ai.json --audit-log ./out/assistantd-dev.log

run-assistant-gui-dev:
	python3 ./assistant/assistant_gui.py

test-assistant-core:
	./scripts/test-assistant-core.sh

build-aifirst-ai-rpm:
	./scripts/build-aifirst-ai-rpm.sh
