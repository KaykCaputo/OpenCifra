SHELL := /bin/bash
.DEFAULT_GOAL := help
PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
BUILDOZER := $(PY) scripts/android.py
PIP := $(PY) -m pip
VERSION := $(shell sed -n 's/^version = //p' buildozer.spec)
TAG ?= v$(VERSION)
REPO ?= KaykCaputo/OpenCifra
ASSETS ?= dist/release
ANDROID_ARTIFACT ?= apk

.PHONY: screenshots help venv install dev run test test-ui lint format check doctor build build-desktop package android-tools android-debug android-release android-deploy android-logcat release-check release-draft release-publish clean

help: ## Show all commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: ## Create the local Python environment
	@test -x "$(PY)" || $(PYTHON) -m venv "$(VENV)"

install: venv ## Install runtime dependencies
	$(PIP) install -r requirements.txt

dev: install ## Install development and desktop packaging tools
	$(PIP) install -r requirements-dev.txt

run: ## Run OpenCifra
	$(PY) main.py

test: ## Run offline unit tests
	$(PY) -m unittest discover -s tests -p 'test_*.py' -v

test-ui: ## Exercise the real UI using Xvfb (Linux)
	KIVY_NO_ARGS=1 KIVY_CLIPBOARD=dummy xvfb-run -a $(PY) tests/ui_smoke.py

screenshots: ## Refresh all four README screenshots from the running UI (Xvfb)
	KIVY_NO_ARGS=1 KIVY_CLIPBOARD=dummy $(PY) scripts/update_screenshots.py

lint: ## Check Python errors and whitespace
	$(PY) -m ruff check .
	git diff --check

format: ## Format Python source
	$(PY) -m ruff format .

check: lint test ## Run all fast checks

doctor: ## Check dependencies and build tools
	$(PY) scripts/doctor.py

build: build-desktop ## Build a native desktop distribution

build-desktop: check ## Package the desktop app for the current OS
	$(PY) -m PyInstaller --noconfirm OpenCifra.spec

package: ## Archive the desktop build and copy Android artifacts with checksums
	$(PY) scripts/release.py package --version "$(VERSION)" --assets "$(ASSETS)"

android-tools: venv ## Install Buildozer and its Python prerequisites
	$(PIP) install 'buildozer>=1.5,<2' 'Cython>=0.29.34,<3' setuptools

android-debug: ## Build an Android debug APK (SDK/NDK downloaded on first run)
	@$(BUILDOZER) android debug

android-release: ## Build a signed APK (ANDROID_ARTIFACT=aab for AAB) using P4A_RELEASE_* environment variables
	$(PY) scripts/release.py signing-check
	@APP_ANDROID_RELEASE_ARTIFACT=$(ANDROID_ARTIFACT) $(BUILDOZER) android release

android-deploy: ## Install and start the debug APK on an attached Android device
	@$(BUILDOZER) android deploy run

android-logcat: ## View Android application logs
	@$(BUILDOZER) android logcat

release-check: check ## Validate clean commit, tag, artifacts and GitHub authentication
	$(PY) scripts/release.py check --tag "$(TAG)" --repo "$(REPO)" --assets "$(ASSETS)"

release-draft: release-check ## Upload artifacts and generated notes to an unpublished GitHub release
	$(PY) scripts/release.py draft --tag "$(TAG)" --repo "$(REPO)" --assets "$(ASSETS)"

release-publish: ## Publish an existing draft release (explicit public action)
	$(PY) scripts/release.py publish --tag "$(TAG)" --repo "$(REPO)" --assets "$(ASSETS)"

clean: ## Remove generated build artifacts (keep .venv, SDK/NDK and user library)
	$(PY) scripts/release.py clean
