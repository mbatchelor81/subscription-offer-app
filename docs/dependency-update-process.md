# Dependency Update Process

This document describes how to safely update Python and Node.js dependencies
for the **subscription-offer-app** project.

---

## Python (Backend — `services/offer-decision-service`)

### 1. Audit current dependencies for known vulnerabilities

```bash
cd services/offer-decision-service
pip install -e '.[audit]'
pip-audit
```

Fix or pin around any reported CVEs before proceeding.

### 2. Update pinned versions

All runtime and dev dependencies are pinned to exact versions in
`pyproject.toml`. To update:

```bash
# Create a fresh virtual environment
python -m venv .venv && source .venv/bin/activate

# Install with loose constraints to resolve latest compatible versions
pip install fastapi uvicorn[standard] openai slowapi

# Record resolved versions
pip freeze | grep -iE 'fastapi|uvicorn|openai|slowapi'

# Update pyproject.toml with the new pinned versions
# Then re-run tests
pip install -e '.[dev]'
pytest tests/ -v
ruff check app/ tests/
```

### 3. Re-audit after update

```bash
pip install -e '.[audit]'
pip-audit
```

---

## Node.js (Frontend — `web/demo-ui`)

### 1. Audit for known vulnerabilities

```bash
cd web/demo-ui
npm audit
```

### 2. Update dependencies

```bash
npm update          # update within semver range
npm audit fix       # auto-fix vulnerabilities where possible
npm audit           # verify remaining issues
```

For major-version bumps:

```bash
npx npm-check-updates -u   # update package.json ranges
npm install                 # resolve & install
npm run build               # verify build still works
```

### 3. Commit lock files

Always commit both `package.json` and `package-lock.json` together so that
CI reproduces the exact dependency tree.

---

## CI Integration

- **pip-audit** runs as part of the `[audit]` optional dependency group.
  Add a CI step: `pip install -e '.[audit]' && pip-audit` to gate merges.
- **npm audit** can be added as a CI step:
  `cd web/demo-ui && npm ci && npm audit --audit-level=high`

---

## Schedule

We recommend running dependency audits:

| Cadence   | Action                             |
|-----------|------------------------------------|
| Weekly    | `pip-audit` and `npm audit` scans  |
| Monthly   | Evaluate minor/patch updates       |
| Quarterly | Evaluate major-version upgrades    |
