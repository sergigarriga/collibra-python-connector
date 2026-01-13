# Contributing to Collibra Python Connector

Thank you for your interest in contributing to the Collibra Python Connector! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Documentation](#documentation)

## Code of Conduct

Please be respectful and considerate in all interactions. We want this to be a welcoming community for everyone.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/collibra-python-connector.git
   cd collibra-python-connector
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/rauldaal/collibra-python-connector.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip or conda for package management

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode with dev dependencies:
   ```bash
   cd collibra_connector
   pip install -e ".[dev]"
   ```

3. Verify installation:
   ```bash
   python -c "from collibra_connector import CollibraConnector; print('OK')"
   ```

### Environment Variables (for integration tests)

If you have access to a Collibra instance for testing:

```bash
export COLLIBRA_URL="https://your-instance.collibra.com"
export COLLIBRA_USERNAME="your-username"
export COLLIBRA_PASSWORD="your-password"
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-bulk-delete` - New features
- `fix/pagination-offset` - Bug fixes
- `docs/improve-readme` - Documentation changes
- `refactor/simplify-auth` - Code refactoring

### Commit Messages

Write clear, concise commit messages:

```
feat: add batch processing for asset creation

- Add BatchProcessor class for bulk operations
- Add BatchResult dataclass for tracking results
- Include progress callback support
```

Use conventional commit prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

## Testing

### Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_connector.py -v
```

Run with coverage:
```bash
pytest tests/ -v --cov=collibra_connector --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names: `test_add_asset_with_valid_uuid()`
- Use pytest fixtures for common setup
- Mock external API calls to avoid hitting real servers

Example test:

```python
import pytest
from unittest.mock import Mock, patch
from collibra_connector import CollibraConnector

class TestAssetCreation:
    @pytest.fixture
    def connector(self):
        return CollibraConnector(
            api="https://test.collibra.com",
            username="testuser",
            password="testpass"
        )

    def test_add_asset_requires_name(self, connector):
        """Test that name is required for asset creation."""
        with pytest.raises(ValueError, match="Name.*required"):
            connector.asset.add_asset(
                name="",
                domain_id="valid-uuid"
            )
```

## Pull Request Process

1. **Update your fork**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make your changes** and commit them

4. **Run tests** to ensure everything passes:
   ```bash
   pytest tests/ -v
   ```

5. **Run type checking**:
   ```bash
   mypy collibra_connector/
   ```

6. **Run linting**:
   ```bash
   ruff check collibra_connector/
   ```

7. **Push your branch**:
   ```bash
   git push origin feature/your-feature
   ```

8. **Open a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what and why
   - Reference to any related issues

### PR Checklist

- [ ] Tests pass locally
- [ ] New code has tests
- [ ] Type hints added for new functions
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated

## Code Style

### General Guidelines

- Follow [PEP 8](https://pep8.org/) style guide
- Maximum line length: 120 characters
- Use type hints for all function signatures
- Write docstrings for all public functions/classes

### Type Hints

```python
from typing import Optional, List, Dict, Any

def get_asset(self, asset_id: str) -> Dict[str, Any]:
    """
    Get an asset by ID.

    Args:
        asset_id: The UUID of the asset.

    Returns:
        Dictionary containing asset details.

    Raises:
        ValueError: If asset_id is not a valid UUID.
        NotFoundError: If asset is not found.
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def process_items(
    items: List[Dict[str, Any]],
    batch_size: int = 50,
    callback: Optional[Callable] = None
) -> BatchResult:
    """
    Process items in batches.

    Args:
        items: List of items to process.
        batch_size: Number of items per batch. Defaults to 50.
        callback: Optional callback function for progress updates.

    Returns:
        BatchResult containing success and error counts.

    Raises:
        ValueError: If items is empty.

    Example:
        >>> result = process_items(my_items, batch_size=100)
        >>> print(f"Processed {result.success_count} items")
    """
    pass
```

### Imports

Order imports as:
1. Standard library
2. Third-party packages
3. Local imports

```python
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from .api import Asset, Community
from .helpers import Paginator
```

## Documentation

### README Updates

When adding new features, update the README.md with:
- Feature description in the Features section
- Usage examples in the appropriate section
- Any new configuration options

### CHANGELOG Updates

Add entries to CHANGELOG.md under the `[Unreleased]` section:

```markdown
## [Unreleased]

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Change description
```

## Questions?

If you have questions, feel free to:
- Open an issue on GitHub
- Contact the maintainer

Thank you for contributing!
