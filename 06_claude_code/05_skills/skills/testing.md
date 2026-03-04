# Testing Conventions

## Framework
Use `pytest`. Config lives in `pyproject.toml` under `[tool.pytest.ini_options]`.

## File Layout
```
src/
  module.py
tests/
  test_module.py      # mirrors src/ structure
  conftest.py         # shared fixtures
```

## Writing Tests
```python
def test_<what>_<condition>():   # descriptive names
    # Arrange
    input_data = ...
    # Act
    result = function_under_test(input_data)
    # Assert
    assert result == expected
```

## Running Tests
```bash
pytest                          # all tests
pytest tests/test_module.py     # single file
pytest -k "test_login"          # by name pattern
pytest -x                       # stop on first failure
pytest --tb=short               # compact tracebacks
pytest -v                       # verbose output
```

## Coverage
```bash
pytest --cov=src --cov-report=term-missing
```
