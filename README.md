# Django Steps

A flexible and extensible Django application for defining and managing dynamic workflows with custom steps, statuses, and CEL-based conditional transitions.

## Overview

Django Steps is a reusable Django application that provides a robust workflow management system. It allows developers to define multi-step workflows with conditional transitions, custom step statuses, and support for essential workflow operations like pausing, resuming, and canceling.

The core idea is to provide a structured way to manage complex processes within a Django application, where a process is composed of several steps, and each step can have multiple statuses. The transitions between steps can be controlled by CEL (Common Expression Language) expressions, allowing for dynamic and flexible workflow logic.

## Key Features

- **Dynamic Workflows**: Define workflows with multiple steps and transitions.
- **Conditional Transitions**: Use CEL expressions to control the flow between steps.
- **Custom Statuses**: Define custom statuses for each step, such as "Pending," "Approved," or "Rejected."
- **Workflow Operations**: Pause, resume, and cancel workflow instances.
- **Generic Association**: Link workflows to any Django model using generic foreign keys.
- **Service-Oriented**: A dedicated service layer to interact with workflow instances.

## How It Works

The application is built around a few key models:

- **`Workflow`**: Represents a workflow definition, such as "Claim Processing" or "User Onboarding."
- **`WorkflowStep`**: Represents a single step within a workflow, like "Submit Claim" or "Verify Documents."
- **`WorkflowStepStatus`**: Defines a custom status for a step, such as "Pending Review" or "Approved."
- **`WorkflowTransition`**: Defines the transition from one step to another, with an optional CEL condition.
- **`WorkflowInstance`**: Represents a running instance of a workflow for a specific Django model.

## Usage

### 1. Define a Workflow

First, you need to define a workflow, its steps, statuses, and transitions. This can be done in the Django admin or programmatically.

Here's an example of how you might define a simple "Claim Processing" workflow:

```
+----------------+      +----------------+      +------------------+
|  Submit Claim  |----->|  Review Claim  |----->|  Approve/Reject  |
+----------------+      +----------------+      +------------------+
 (Initial Step)                              (Final Step)
```

- **Workflow**: "Claim Processing"
- **Steps**:
  1. "Submit Claim" (Initial Step)
  2. "Review Claim"
  3. "Approve/Reject" (Final Step)

- **Statuses**:
  - For "Submit Claim": "Submitted" (Completion Status)
  - For "Review Claim": "Under Review" (Default), "Approved" (Completion), "Rejected" (Completion)
  - For "Approve/Reject": "Approved" (Completion), "Rejected" (Completion)

- **Transitions**:
  - From "Submit Claim" to "Review Claim" (unconditional)
  - From "Review Claim" to "Approve/Reject" (unconditional)

### 2. Start a Workflow Instance

To start a workflow for a specific object (e.g., a `Claim` model), you can use the `start_workflow_instance` service function:

```python
from django_steps.services import start_workflow_instance
from myapp.models import Claim

claim = Claim.objects.get(id=123)
workflow_instance = start_workflow_instance(
    workflow_name="Claim Processing",
    content_object=claim
)
```

### 3. Update Step Status

As the object moves through the process, you can update the status of the current step. If the new status is a "completion status," the workflow will automatically transition to the next step.

```python
from django_steps.services import update_workflow_step_status

# This will move the workflow to the "Review Claim" step
update_workflow_step_status(
    workflow_instance=workflow_instance,
    new_status_name="Submitted"
)
```

If a transition has a condition, you can provide context data for the CEL evaluation:

```python
# Example of a conditional transition
# Condition: "claim.amount > 1000"
update_workflow_step_status(
    workflow_instance=workflow_instance,
    new_status_name="Approved",
    context_data={"claim": {"amount": 1500}}
)
```

### 4. Workflow Operations

You can also pause, resume, or cancel a workflow instance:

```python
from django_steps.services import (
    set_workflow_on_hold,
    resume_workflow_instance,
    cancel_workflow_instance
)

# Pause the workflow
set_workflow_on_hold(workflow_instance)

# Resume the workflow
resume_workflow_instance(workflow_instance)

# Cancel the workflow
cancel_workflow_instance(workflow_instance)
```

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