# AutoBench AGENTS.md

This file provides guidelines for agentic coding agents working in this repository.

---

## Project Overview

AutoBench is an agentic benchmark for evaluating LLMs as Bengaluru auto-rickshaw drivers. It simulates a 30-day period where an LLM makes decisions about accepting rides, managing time, and maximizing profits.

- **Python**: 3.13+
- **Package Manager**: uv
- **Linter**: Ruff
- **Key Dependencies**: openai, pandas, pydantic, requests

---

## Build / Lint / Test Commands

### Installation

```bash
# Install dependencies with uv
uv sync
```

### Running the Application

```bash
# Run the main benchmark
python main.py

# With custom arguments
python main.py --model gpt-4o-mini --days 30 --output results/
```

### Linting

```bash
# Run ruff linter
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

### Testing

> **Note**: No tests currently exist in this repository. When tests are added:

```bash
# Run all tests (pytest assumed)
pytest

# Run a single test
pytest tests/test_file.py::test_function_name
pytest -k "test_function_name"
```

---

## Code Style Guidelines

### Imports

Organize imports in the following order, separated by blank lines:

1. Standard library (`json`, `pathlib`, `random`)
2. Third-party packages (`pydantic`, `typing`)
3. Local application imports (`src.data`, `src.simulation`)

```python
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field

from src.data.locations import get_locations_by_type, get_all_types
from src.data.routes import get_route
from src.simulation.traffic import get_traffic_multiplier
```

### Formatting

- Use Ruff with default settings (line length 88)
- Use Black-compatible formatting
- Use single quotes for strings unless double quotes are needed
- Trailing commas for multi-line collections

### Type Hints

- Always use type hints for function parameters and return types
- Use `Optional[X]` instead of `X | None` for broader compatibility
- Use `Dict`, `List` from typing for Python 3.9+ compatibility, or native `dict`, `list` for Python 3.13+

```python
def get_route(origin: str, destination: str) -> Dict[str, float]:
    ...

def generate_ping(
    current_time: str,
    day_of_week: int,
    current_location: str,
    shift_remaining_min: int,
) -> Optional[RideRequest]:
    ...
```

### Naming Conventions

- **Classes**: PascalCase (`GameState`, `RideRequest`, `RideEvent`)
- **Functions/variables**: snake_case (`get_route`, `calculate_fare`, `current_time`)
- **Constants**: SCREAMING_SNAKE_CASE (`SHIFT_DURATION_MINUTES`, `DAY_NAMES`)
- **Private functions**: prefix with underscore (`_internal_helper`)

### Pydantic Models

- Use `BaseModel` for data transfer objects
- Use `Field` for fields with default factories or validation
- Use descriptive field names matching the data they represent

```python
class RideEvent(BaseModel):
    origin: str
    destination: str
    distance_km: float
    base_duration_min: float
    simulated_duration_min: float
    fare: float
    fuel_cost: float
    profit: float
    time_started: str
    time_ended: str


class GameState(BaseModel):
    current_day: int = 1
    current_time: str = "05:00"
    rides_history: List[RideEvent] = Field(default_factory=list)
```

### Error Handling

- Use specific exception types (`KeyError`, `ValueError`, `FileNotFoundError`)
- Provide descriptive error messages
- Handle expected failures gracefully (return `None` when appropriate)

```python
try:
    route = get_route(current_location, dest.name)
except KeyError:
    return None

try:
    with open(BASE_ROUTES_PATH, "r") as f:
        _routes_cache = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(f"Routes file not found: {BASE_ROUTES_PATH}")
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON in routes file: {e}")
```

### Function Design

- Keep functions focused and single-purpose
- Use early returns to reduce nesting
- Document complex logic with inline comments only when necessary
- Prefer pure functions where possible for testability

### Module Structure

```
src/
├── __init__.py           # Package marker
├── data/                 # Data loading (locations, routes)
│   ├── __init__.py
│   ├── locations.py
│   └── routes.py
├── simulation/           # Core simulation logic
│   ├── __init__.py
│   ├── dispatcher.py    # Ride generation
│   ├── fares.py         # Fare calculation
│   ├── fuel.py          # Fuel cost calculation
│   ├── shift.py         # Shift management
│   ├── state.py         # Game state management
│   └── traffic.py       # Traffic simulation
├── llm/                  # LLM integration (future)
│   ├── client.py
│   └── prompts.py
├── benchmark/            # Benchmark runner (future)
│   ├── runner.py
│   └── history.py
└── output/               # Output handling (future)
    └── logger.py
```

### Testing Patterns

When adding tests:

- Place tests in a `tests/` directory at project root
- Use `pytest` as the test framework
- Name test files `test_*.py` or `*_test.py`
- Use descriptive test function names: `test_calculate_fare_returns_minimum_for_short_ride`
- Use fixtures for common setup
- Mock external dependencies (API calls, file I/O)

```python
import pytest
from src.simulation.fares import calculate_fare

def test_calculate_fare_returns_minimum_for_short_ride():
    assert calculate_fare(1.5, "08:30") == 36.0

def test_calculate_fare_applies_night_multiplier():
    assert calculate_fare(10, "23:00") == 270.0  # 54 + 8*27
```

### Git Conventions

- Make commits atomic and descriptive
- Use conventional commit format: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- Never commit secrets (API keys, credentials) - use `.env` files
- Add `env` and cache directories to `.gitignore`

---

## Common Development Tasks

### Adding a New Simulation Module

1. Create `src/simulation/<module_name>.py`
2. Add imports following the standard order
3. Define functions with type hints
4. Add unit tests in `tests/test_<module_name>.py`
5. Run `ruff check .` to verify code quality

### Adding a New Data Source

1. Place data files in project root or `data/` directory
2. Create loader functions in `src/data/`
3. Add caching if data is expensive to load
4. Handle missing/invalid data gracefully with appropriate errors

### Running a Single Test

```bash
# By test function name
pytest -k "test_function_name"

# By file and function
pytest tests/test_file.py::test_function_name

# By exact test node id
pytest tests/test_file.py::TestClass::test_method
```

---

## Dependencies

- **openai**: LLM API client
- **pandas**: Data manipulation
- **pydantic**: Data validation and settings
- **requests**: HTTP client for API calls

---

## Environment Variables

Create a `.env` file for API credentials:

```
OPENAI_API_KEY=sk-...
BASE_URL=https://synthetic.new/v1
```

Never commit `.env` files to version control.
