======================
Django Steps
======================

A workflow management application for Django projects

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview
--------

Django Steps is a reusable Django application that provides a flexible workflow management system. It allows defining multi-step workflows with conditional transitions, different step statuses, and supports workflow operations like pausing, resuming, and cancelling.

Key Features
-----------

- Create and manage workflow definitions with multiple steps
- Define transitions between steps with conditional logic using CEL expressions
- Track status of objects moving through workflows
- Support for workflow operations (pause, resume, cancel)
- Generic content type relationships to associate workflows with any model
- Django admin integration

Models
------

Workflow
~~~~~~~

Represents a complete workflow definition.

.. code-block:: python

    class Workflow(models.Model):
        name = models.CharField(max_length=100)
        description = models.TextField(blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

WorkflowStep
~~~~~~~~~~~

Represents an individual step within a workflow.

.. code-block:: python

    class WorkflowStep(models.Model):
        workflow = models.ForeignKey(Workflow, related_name='steps', on_delete=models.CASCADE)
        name = models.CharField(max_length=100)
        description = models.TextField(blank=True)
        order = models.PositiveIntegerField()
        is_initial_step = models.BooleanField(default=False)
        is_final_step = models.BooleanField(default=False)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

WorkflowStepStatus
~~~~~~~~~~~~~~~~

Defines possible statuses for each step in a workflow.

.. code-block:: python

    class WorkflowStepStatus(models.Model):
        step = models.ForeignKey(WorkflowStep, related_name='possible_statuses', on_delete=models.CASCADE)
        name = models.CharField(max_length=100)
        description = models.TextField(blank=True)
        is_default_status = models.BooleanField(default=False)
        is_completion_status = models.BooleanField(default=False)
        is_cancellation_status = models.BooleanField(default=False)
        is_on_hold_status = models.BooleanField(default=False)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

WorkflowTransition
~~~~~~~~~~~~~~~~

Defines possible transitions between workflow steps with conditions.

.. code-block:: python

    class WorkflowTransition(models.Model):
        workflow = models.ForeignKey(Workflow, related_name='transitions', on_delete=models.CASCADE)
        from_step = models.ForeignKey(WorkflowStep, related_name='outgoing_transitions', on_delete=models.CASCADE)
        to_step = models.ForeignKey(WorkflowStep, related_name='incoming_transitions', on_delete=models.CASCADE)
        condition = models.TextField(blank=True, help_text="CEL expression that must evaluate to true for this transition")
        priority = models.IntegerField(default=0, help_text="Higher priority transitions are evaluated first")
        description = models.TextField(blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

WorkflowInstance
~~~~~~~~~~~~~~

Represents an active workflow for a specific object.

.. code-block:: python

    class WorkflowInstance(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        workflow = models.ForeignKey(Workflow, related_name='instances', on_delete=models.PROTECT)
        current_step = models.ForeignKey(WorkflowStep, null=True, blank=True, on_delete=models.PROTECT)
        current_step_status = models.ForeignKey(WorkflowStepStatus, null=True, blank=True, on_delete=models.PROTECT)
        started_at = models.DateTimeField(null=True, blank=True)
        completed_at = models.DateTimeField(null=True, blank=True)
        content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
        object_id = models.CharField(max_length=255)  # Supporting UUID strings
        content_object = GenericForeignKey('content_type', 'object_id')

Service Functions
----------------

The module provides several service functions to work with workflows:

start_workflow_instance
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def start_workflow_instance(workflow_name: str, content_object) -> WorkflowInstance | None:
        """Starts a new workflow instance for a given content object and workflow name."""

update_workflow_step_status
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def update_workflow_step_status(workflow_instance: WorkflowInstance, new_status_name: str, context_data: dict = None) -> bool:
        """Updates the current step's status for a given workflow instance."""

cancel_workflow_instance
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def cancel_workflow_instance(workflow_instance: WorkflowInstance) -> bool:
        """Attempts to cancel a workflow instance."""

set_workflow_on_hold
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def set_workflow_on_hold(workflow_instance: WorkflowInstance) -> bool:
        """Attempts to put a workflow instance on hold."""

resume_workflow_instance
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def resume_workflow_instance(workflow_instance: WorkflowInstance) -> bool:
        """Attempts to resume a workflow instance from an on-hold state."""

get_workflow_instance_for_object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def get_workflow_instance_for_object(content_object, workflow_name: str | None = None) -> WorkflowInstance | None:
        """Retrieves a workflow instance associated with a given content object."""

Usage Example
-------------

Here's an example of how to use Django Steps in your project:

1. Define your workflow structure in the Django admin:
   - Create a Workflow
   - Add WorkflowSteps with appropriate order and flags
   - Define WorkflowStepStatus entries for each step
   - Create WorkflowTransitions between steps with CEL conditions

2. Start a workflow for an object:

.. code-block:: python

    from django_steps.services import start_workflow_instance

    # Start a workflow for a model instance
    instance = start_workflow_instance("My Workflow", my_model_instance)

3. Update workflow status with context data for conditional transitions:

.. code-block:: python

    from django_steps.services import update_workflow_step_status

    # Update status with context data for CEL conditions
    update_workflow_step_status(instance, "Approved", context_data={
        "claim": {"amount": 5000, "is_high_risk": False}
    })

4. Manage workflow state:

.. code-block:: python

    from django_steps.services import set_workflow_on_hold, resume_workflow_instance, cancel_workflow_instance

    # Put workflow on hold
    set_workflow_on_hold(instance)

    # Resume workflow
    resume_workflow_instance(instance)

    # Cancel workflow
    cancel_workflow_instance(instance)

CEL Expressions
--------------

Workflow transitions use Common Expression Language (CEL) conditions to determine which path to take. When updating a workflow status that completes a step, the system evaluates all outgoing transitions and follows the first one with a condition that evaluates to true.

Examples of CEL expressions:

- ``claim.is_high_risk == true`` - Condition for high-risk claims
- ``claim.amount > 10000`` - Condition for high-value claims
- ``claim.status_field == "Approved"`` - Condition for approved items

The context data provided to the ``update_workflow_step_status`` function is available in CEL expressions.

Admin Interface
--------------

Django Steps includes Django Admin integration that allows administrators to:

- Define and manage workflows and their steps
- Configure step statuses and transitions
- View and manage workflow instances
- Perform operations on workflows (hold, resume, cancel)

Extending Django Steps
--------------------

You can extend Django Steps for more complex use cases by:

1. Creating custom services that use the core workflow functions
2. Adding custom admin actions for specific workflow operations
3. Implementing signals to respond to workflow state changes
4. Extending models with additional fields or behaviors

For more advanced customization, consider subclassing the existing models or creating proxy models.
