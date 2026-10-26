# PJM GATS Home Assistant Integration - Agent Guide

## Project Overview

Custom Home Assistant integration for PJM GATS. Scrapes the PJM GATS web portal to expose sensor data (generation, certificates, generator info) in Home Assistant.

## Project Structure

```
pjm_gats/
├── custom_components/pjm_gats/     # HA integration code
│   ├── __init__.py                 # async_setup_entry, async_unload_entry
│   ├── config_flow.py              # Config flow with validate_input
│   ├── coordinator.py              # PjmGatsClient + PjmGatsDataUpdateCoordinator
│   ├── sensor.py                   # Sensor entities (12 sensors)
│   └── const.py                    # DOMAIN constant
├── tests/                          # Unit tests (pytest)
│   ├── conftest.py                 # Shared fixtures
│   ├── test_config_flow.py         # validate_input tests
│   ├── test_coordinator.py         # Coordinator logic tests
│   ├── test_init.py                # Setup/unload tests
│   └── test_sensor.py              # Sensor entity tests
├── pyproject.toml                  # Tool config (ruff, mypy, pytest, etc.)
├── .pre-commit-config.yaml         # Pre-commit hooks
└── requirements.txt                # beautifulsoup4
```

## Quick Commands

### Run Tests

```bash
uv run pytest tests/ -v
```

### Linting

```bash
# Ruff (fast linter + formatter)
uv run ruff check custom_components/ tests/
uv run ruff check --fix custom_components/ tests/
uv run ruff format custom_components/ tests/

# MyPy (type checking)
uv run mypy custom_components/pjm_gats/

# Pylint
uv run pylint custom_components/pjm_gats/

# All pre-commit hooks (may fail on older git due to --deduplicate flag)
uv run pre-commit run --all-files
```

### Install Dev Dependencies

```bash
uv sync --all-extras
```

## Architecture Notes

### Coordinator Pattern

- `PjmGatsClient`: Async aiohttp client with CSRF login + BeautifulSoup parsing
- `PjmGatsDataUpdateCoordinator`: HA DataUpdateCoordinator (30-min interval)
- Errors: `ConfigEntryAuthFailed` for auth, `UpdateFailed` for API errors

### Key Implementation Details

- **No file-based cookie persistence** - uses aiohttp session cookies in memory
- **CSRF token scraping** from login page before POST
- **Session validation** via home page check before each data fetch
- **Runtime data** stored on `config_entry.runtime_data` (coordinator)

### Sensor Entities (12 total)

| Key                            | Description            |
| ------------------------------ | ---------------------- |
| `generation_mwh`               | Total generation (MWh) |
| `certificates_active`          | Active certificates    |
| `certificates_ceps`            | CEPS certificates      |
| `certificates_on_bb`           | On Bulletin Board      |
| `certificates_reserved`        | Reserved certificates  |
| `certificates_total`           | Total certificates     |
| `certificates_active_hourly`   | Active hourly (MWh)    |
| `certificates_ceps_hourly`     | CEPS hourly (MWh)      |
| `certificates_reserved_hourly` | Reserved hourly (MWh)  |
| `generator_id`                 | Generator unit ID      |
| `generator_plant`              | Plant name             |
| `generator_status`             | ACT/INACT/PEND/RET     |

## Testing in Real Home Assistant

### Install Custom Component

```bash
# Copy to HA config directory
cp -r custom_components/pjm_gats/ /path/to/ha/config/custom_components/

# Restart HA (or use Developer Tools → YAML → Restart Custom Components)
```

### Configure Integration

1. Settings → Devices & Services → Add Integration
2. Search "PJM GATS"
3. Enter PJM GATS username/password

### Verify

- Check **Developer Tools → States** for `sensor.pjm_gats_*` entities
- Force refresh: Settings → Devices & Services → PJM GATS → Configure → Reload

## Common Issues

| Issue                                         | Solution                                                                |
| --------------------------------------------- | ----------------------------------------------------------------------- |
| Pre-commit `git ls-files --deduplicate` fails | Git version < 2.43; run tools directly instead                          |
| Pylint `unexpected-keyword-arg` on sensors    | HA dynamic typing; disabled with `# pylint: disable=...`                |
| Integration not found in HA                   | Ensure folder is `custom_components/pjm_gats/` (not `pjm_gats/` inside) |

## Code Style

- Python 3.14.9 (see `.python-version`)
- Ruff: line-length=100, target-version=py314
- MyPy: strict=true
- Imports: Ruff I001 (isort) with known-first-party
