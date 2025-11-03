# AGENTS.md

## Python Project Code Quality Guidelines

- All import statements must be at the top of each file, before any code, functions, or classes.
- Do not use inline or function-local imports unless absolutely necessary (e.g., to avoid circular imports or for optional dependencies).
- Use pytest fixtures for setup/teardown and to avoid code duplication in tests.
- Use `pytest.mark.parametrize` to cover multiple test cases with a single test function.
- Remove code duplication in test helpers by moving repeated logic into fixtures or helper functions.
- Keep all test and helper code DRY (Don't Repeat Yourself).
- Ensure all files are formatted and linted according to project standards.
- Review and refactor regularly for maintainability and clarity.

## Example (for tests)

```python
import pytest
from mymodule import myfunc

@pytest.fixture
def resource():
    ...

@pytest.mark.parametrize("input,expected", [(1,2),(2,3)])
def test_myfunc(resource, input, expected):
    assert myfunc(input) == expected
```

---

**All contributors and agents must follow these rules.**
