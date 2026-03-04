# Python Conventions

## Style
- Formatter: `ruff format` (line length 100)
- Linter: `ruff check` (rules: E, F, I)
- Type hints on all public functions
- Docstrings on public classes and functions (one-line for simple functions)

## Project Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Imports Order (enforced by ruff/isort)
1. Standard library
2. Third-party packages
3. Local imports
(blank line between each group)

## Error Handling
- Raise specific exceptions, not bare `Exception`
- Use `logging` not `print` in library code
- Context managers (`with`) for resources

## Common Patterns
```python
# Path handling
from pathlib import Path
path = Path(__file__).parent / "data" / "file.json"

# Dataclasses for structured data
from dataclasses import dataclass, field

@dataclass
class Config:
    host: str = "localhost"
    port: int = 8080
    tags: list[str] = field(default_factory=list)
```
