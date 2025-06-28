# Django Steps

A workflow management application for Django projects.

## Overview

Django Steps is a reusable Django application that provides a flexible workflow management system. It allows defining multi-step workflows with conditional transitions, different step statuses, and supports workflow operations like pausing, resuming, and cancelling.

## Test Suite

This project uses pytest for testing. The test suite is structured as follows:

- `/tests/` - The main test directory
  - `conftest.py` - Shared pytest fixtures
  - `test_models.py` - Tests for model functionality and validation
  - `test_workflow_operations.py` - Tests for workflow instance operations
  - `test_services.py` - Tests for service layer functions
  - `pytest.ini` - Pytest configuration

## Running Tests

To run the tests, use:

```bash
pytest
```

Or to run a specific test file:

```bash
pytest tests/test_models.py
```

## Documentation

Documentation is available in the `/docs/` directory.

```bash
cd docs
make html
```

Then open `_build/html/index.html` in your browser.
