import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured

from .utils import extract_context_data_from_content_object

logger = logging.getLogger(__name__)


class Workflow(models.Model):
    """
    Represents a definable workflow, e.g., "Fast-track", "Investigation", "Litigation".
    Each workflow consists of multiple ordered steps.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="The unique name of the workflow (e.g., 'Investigation').",
    )
    description = models.TextField(
        blank=True, help_text="A brief description of what this workflow entails."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Workflow"
        verbose_name_plural = "Workflows"
        ordering = ["name"]  # Order workflows alphabetically by name

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    """
    Represents an individual step within a Workflow.
    Steps are ordered to define the sequence of the workflow.
    """

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="steps",  # Allows accessing steps from a Workflow instance: workflow.steps.all()
        help_text="The workflow this step belongs to.",
    )
    name = models.CharField(
        max_length=255,
        help_text="The name of the step (e.g., 'Interview Stakeholders').",
    )
    description = models.TextField(
        blank=True, help_text="A detailed description of this specific step."
    )
    order = models.PositiveIntegerField(
        help_text="The order of this step within the workflow (e.g., 1 for the first step, 2 for the second)."
    )
    is_initial_step = models.BooleanField(
        default=False,
        help_text="Designates if this is the very first step of the workflow. "
        "There should typically be only one initial step per workflow.",
    )
    is_final_step = models.BooleanField(
        default=False,
        help_text="Designates if this is the last step of the workflow. "
        "Once an instance reaches this step, it can be marked as complete.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Workflow Step"
        verbose_name_plural = "Workflow Steps"
        # Ensure unique order per workflow and order steps correctly
        unique_together = (("workflow", "order"),)
        ordering = ["workflow", "order"]

    def __str__(self):
        return f"{self.workflow.name}: {self.name} (Order: {self.order})"


class WorkflowStepStatus(models.Model):
    """
    Defines a custom status option for a specific WorkflowStep.
    """

    step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="possible_statuses",
        help_text="The workflow step this status option belongs to.",
    )
    name = models.CharField(
        max_length=50,
        help_text="The name of the status (e.g., 'Pending Review', 'Approved', 'Rejected').",
    )
    description = models.TextField(
        blank=True, help_text="A description of this status."
    )
    is_default_status = models.BooleanField(
        default=False,
        help_text="If checked, this status will be automatically assigned when the workflow instance "
        "enters this step. There should be only one default status per step.",
    )
    is_completion_status = models.BooleanField(
        default=False,
        help_text="If checked, reaching this status marks the completion of the current step, "
        "potentially allowing the workflow instance to advance to the next step, "
        "or marking the workflow as complete if it's the final step.",
    )
    is_cancellation_status = models.BooleanField(
        default=False,
        help_text="If checked, this status represents a 'cancelled' state for the workflow instance. "
        "There should be only one cancellation status per step.",
    )
    is_on_hold_status = models.BooleanField(
        default=False,
        help_text="If checked, this status represents an 'on hold' state for the workflow instance. "
        "There should be only one on-hold status per step.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Workflow Step Status"
        verbose_name_plural = "Workflow Step Statuses"
        unique_together = (
            ("step", "name"),
        )
        ordering = ["step", "name"]

        constraints = [
            # Ensure only one default status per step
            models.UniqueConstraint(
                fields=["step"],
                condition=models.Q(is_default_status=True),
                name="unique_default_status_per_step"
            ),
            # Ensure only one cancellation status per step
            models.UniqueConstraint(
                fields=["step"],
                condition=models.Q(is_cancellation_status=True),
                name="unique_cancellation_status_per_step"
            ),
            # Ensure only one on-hold status per step
            models.UniqueConstraint(
                fields=["step"],
                condition=models.Q(is_on_hold_status=True),
                name="unique_on_hold_status_per_step"
            ),
        ]

    def __str__(self):
        return f"{self.step.workflow.name} - {self.step.name}: {self.name}"


class WorkflowTransition(models.Model):
    """
    Defines a possible transition from one WorkflowStep to another, based on a CEL condition.
    """

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="transitions",
        help_text="The workflow this transition belongs to.",
    )
    from_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="outgoing_transitions",
        help_text="The step from which this transition originates.",
    )
    to_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE,
        related_name="incoming_transitions",
        help_text="The step to which this transition leads.",
    )
    condition = models.TextField(
        blank=True,
        help_text="CEL expression that must evaluate to true for this transition to be taken. "
        "Example: 'claim.amount > 1000 && claim.priority == \"high\"'. "
        "Leave empty for unconditional transition (if multiple, order matters).",
    )
    priority = models.IntegerField(
        default=0,
        help_text="Higher priority transitions are evaluated first if multiple conditions could be met. "
        "Use 0 for normal, positive for higher priority.",
    )
    description = models.TextField(
        blank=True,
        help_text="A description of this transition, explaining its purpose or the condition.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Workflow Transition"
        verbose_name_plural = "Workflow Transitions"
        # Ensure that for a given from_step, there's no identical to_step with the same condition
        unique_together = (
            ("from_step", "to_step", "priority"),
        )  # Ensure unique priority per from_step, to_step pair
        ordering = ["from_step", "-priority"]  # Evaluate higher priority first

    def __str__(self):
        return f"Transition from '{self.from_step.name}' to '{self.to_step.name}' ({self.workflow.name})"


class WorkflowInstance(models.Model):
    """
    Represents a specific ongoing execution of a Workflow for a particular object.
    Uses Django's ContentType framework to link to any other model in the project.
    """

    # Using AutoField instead of UUIDField to avoid type conversion issues
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.PROTECT,  # Prevent deleting a workflow if instances exist
        related_name="instances",
        help_text="The type of workflow being executed (e.g., 'Investigation').",
    )
    current_step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.SET_NULL,  # If a step is deleted, set to null (or handle more rigorously)
        null=True,
        blank=True,
        related_name="current_instances",
        help_text="The current step this workflow instance is at.",
    )
    current_step_status = models.ForeignKey(
        WorkflowStepStatus,
        on_delete=models.SET_NULL,  # If a step status is deleted, set to null
        null=True,
        blank=True,
        related_name="instances_at_status",
        help_text="The current custom status of the workflow instance within its current step.",
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this workflow instance was initiated.",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when this workflow instance was completed (if applicable).",
    )

    # Generic Foreign Key to link to any Django model
    # For example, if linking to a 'Claim' model:
    # content_type = ContentType.objects.get_for_model(Claim)
    # object_id = claim_instance.id
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The ContentType of the object this workflow instance is for.",
    )
    object_id = models.IntegerField(
        help_text="The ID of the object this workflow instance is associated with (e.g., a Claim ID).",
    )
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = "Workflow Instance"
        verbose_name_plural = "Workflow Instances"
        # Ensure only one active workflow instance of a specific type per object
        unique_together = (("workflow", "content_type", "object_id"),)
        ordering = ["-started_at"]  # Order by most recently started

    def __str__(self):
        object_repr = getattr(
            self.content_object, "__str__", lambda: f"ID: {self.object_id}"
        )()
        current_step_name = self.current_step.name if self.current_step else "N/A Step"
        current_step_status_name = (
            self.current_step_status.name if self.current_step_status else "N/A Status"
        )
        return (
            f"Instance of '{self.workflow.name}' for {self.content_type.model} "
            f"('{object_repr}') - Step: {current_step_name} - Status: {current_step_status_name}"
        )

    def start_workflow(self):
        """
        Initializes the workflow instance by setting its current step to the
        first step of the associated workflow and its step-specific status.
        """
        # A workflow instance is considered 'pending' if it hasn't started yet (current_step is None)
        if self.current_step is not None:
            logger.info(f"Workflow '{self.workflow.name}' already started.")
            return False

        try:
            # Get the first step (is_initial_step=True)
            first_step = self.workflow.steps.filter(is_initial_step=True).first()
            if not first_step:
                raise ImproperlyConfigured(
                    f"Workflow '{self.workflow.name}' has no steps defined or no initial step."
                )

            # Get the default status for the first step
            default_step_status = first_step.possible_statuses.filter(
                is_default_status=True
            ).first()
            if not default_step_status:
                raise ImproperlyConfigured(
                    f"First step '{first_step.name}' has no default status defined. "
                    "Please define one default status for each step."
                )

            self.current_step = first_step
            self.current_step_status = default_step_status
            self.save()
            logger.debug(f"Started workflow '{self.workflow.name}' for object {self.object_id}")
            return True

        except ImproperlyConfigured as e:
            logger.error(str(e))
            return False

    def update_step_status(
        self, new_status_name, context_data: dict = None
    ):
        """
        Updates the current step's status for this workflow instance.
        If the new status is a 'completion status' for the current step,
        it attempts to advance the workflow to the next step or mark it as completed.

        Args:
            new_status_name (str): The name of the new WorkflowStepStatus.
            context_data (dict, optional): Data to provide to CEL expressions for evaluation.
                                          If None, it will attempt to extract from content_object.
        """
        if self.is_completed():
            logger.info(f"Workflow '{self.workflow.name}' is already completed.")
            return False

        if not self.current_step:
            logger.error("Workflow instance has no current step. Call start_workflow() first.")
            return False

        new_step_status = self.current_step.possible_statuses.filter(
            name=new_status_name
        ).first()
        if not new_step_status:
            logger.error(
                f"Status '{new_status_name}' is not a valid status for step '{self.current_step.name}'."
            )
            return False

        self.current_step_status = new_step_status
        self.save()
        logger.debug(f"Updated workflow '{self.workflow.name}' status to '{new_status_name}'")

        # If the new status is a completion status, attempt to advance the workflow
        if new_step_status.is_completion_status:
            # Pass context_data directly to the _advance_to_next_workflow_step method
            return self._advance_to_next_workflow_step(context_data=context_data)

        return True  # Status updated, but workflow did not advance

    def _advance_to_next_workflow_step(self, context_data: dict = None):
        """
        Internal method to move the workflow instance to the next workflow step based on defined transitions.
        Marks the workflow as completed if it reaches the final step and its completion status.
        This method is typically called after a step reaches a 'completion status'.

        Args:
            context_data (dict, optional): Data to provide to CEL expressions for evaluation.
                                          If None, attempts to extract from content_object.
        """
        # Lazy import to avoid circular dependencies and ensure celparser is installed
        from celparser.evaluator import evaluate
        from celparser.parser import parse

        if not self.current_step:
            logger.error("Workflow instance has no current step to advance from.")
            return False

        # If it's the final step and the status marks completion, then the workflow is truly done.
        if (
            self.current_step.is_final_step
            and self.current_step_status.is_completion_status
        ):
            self.completed_at = timezone.now()
            self.save()
            logger.info(
                f"Workflow '{self.workflow.name}' for object '{self.object_id}' completed."
            )
            return True
        elif (
            self.current_step.is_final_step
            and not self.current_step_status.is_completion_status
        ):
            logger.warning(
                f"Current step '{self.current_step.name}' is final, but current status "
                f"'{self.current_step_status.name}' is not a completion status. Workflow not marked complete."
            )
            return False

        # Attempt to find the next step via transitions
        transitions = self.current_step.outgoing_transitions.all().order_by(
            "-priority"
        )  # Order by priority, highest first

        logger.debug(f"Transaction are: {transitions}")

        evaluated_next_step = None

        # Prepare context for CEL evaluation
        if context_data is None:
            context_data = {}

        # If context_data is empty or doesn't have expected structure, try to extract from content_object
        if not context_data and self.content_object:
            context_data = extract_context_data_from_content_object(self.content_object)

        logger.debug(f"Context data is: {context_data}")

        for transition in transitions:
            if not transition.condition:  # Unconditional transition
                evaluated_next_step = transition.to_step
                logger.info(
                    f"Unconditional transition from '{self.current_step.name}' to '{transition.to_step.name}' taken."
                )
                break

            try:
                # Parse the CEL expression
                parsed_expression = parse(transition.condition)
                result = evaluate(parsed_expression, context_data)
                if result:
                    evaluated_next_step = transition.to_step
                    logger.info(
                        f"Transition from '{self.current_step.name}' to '{transition.to_step.name}' taken. "
                        f"Condition: '{transition.condition}' evaluated to TRUE."
                    )
                    break  # Take the first matching transition (due to priority ordering)
                else:
                    logger.debug(
                        f"Condition '{transition.condition}' evaluated to FALSE for transition to '{transition.to_step.name}'."
                    )
            except Exception as e:
                logger.error(
                    f"Error evaluating CEL condition '{transition.condition}' for transition to '{transition.to_step.name}': {e}"
                )
                # Log the error but continue trying other transitions if parsing/evaluation fails
                continue

        if evaluated_next_step:
            # Find the default status for the next step
            default_next_step_status = evaluated_next_step.possible_statuses.filter(
                is_default_status=True
            ).first()
            if not default_next_step_status:
                error_msg = f"Next step '{evaluated_next_step.name}' has no default status defined. Please define one default status for each step."
                logger.error(error_msg)
                raise ImproperlyConfigured(error_msg)

            self.current_step = evaluated_next_step
            self.current_step_status = default_next_step_status
            self.save()
            return True
        else:
            logger.warning(
                f"No valid transition found from '{self.current_step.name}' for workflow '{self.workflow.name}'. "
                "Workflow instance will remain at current step. Check WorkflowTransition definitions."
            )
            return False

    def is_completed(self):
        """
        Checks if the workflow instance has reached a completed state.
        This is determined if it is on the final step and its current status
        is marked as a completion status.
        """
        return (
            self.current_step is not None
            and self.current_step.is_final_step
            and self.current_step_status is not None
            and self.current_step_status.is_completion_status
        )

    def cancel_workflow(self):
        """
        Attempts to cancel the workflow by setting its current step status to a cancellation status.
        The workflow instance will be marked as completed (cancelled) if successful.
        """
        if self.is_completed():
            logger.info(
                f"Cannot cancel workflow '{self.workflow.name}' as it is already completed."
            )
            return False

        if self.current_step_status and self.current_step_status.is_cancellation_status:
            logger.info(
                f"Workflow '{self.workflow.name}' is already in a cancellation status."
            )
            return True

        # Ensure current_step is not None
        if not self.current_step:
            logger.error(f"Cannot cancel workflow '{self.workflow.name}' as it has no current step.")
            return False

        # Find a final step in the workflow
        final_step = self.workflow.steps.filter(is_final_step=True).first()
        if not final_step:
            logger.error(f"Cannot cancel workflow '{self.workflow.name}' as it has no final step defined.")
            return False

        cancellation_status = self.current_step.possible_statuses.filter(
            is_cancellation_status=True
        ).first()
        if not cancellation_status:
            # Create a cancellation status for the final step if one doesn't exist
            cancellation_status = WorkflowStepStatus.objects.create(
                step=final_step,
                name="Cancelled",
                is_cancellation_status=True,
                is_completion_status=True,
            )
            logger.info(
                f"Created cancellation status for final step '{final_step.name}' in workflow '{self.workflow.name}'."
            )

        # Move to final step with cancellation status
        self.current_step = final_step
        self.current_step_status = cancellation_status
        self.completed_at = timezone.now()  # Mark cancellation time
        self.save()

        logger.info(
            f"Workflow '{self.workflow.name}' for object '{self.object_id}' has been cancelled and moved to final step."
        )
        return True


    def set_on_hold(self):
        """
        Attempts to put the workflow on hold by setting its current step status to an on-hold status.
        """
        if self.is_completed():
            logger.info(
                f"Cannot set workflow '{self.workflow.name}' on hold as it is completed."
            )
            return False

        if self.current_step_status and self.current_step_status.is_on_hold_status:
            logger.info(f"Workflow '{self.workflow.name}' is already on hold.")
            return False

        on_hold_status = self.current_step.possible_statuses.filter(
            is_on_hold_status=True
        ).first()
        if on_hold_status:
            self.current_step_status = on_hold_status
            self.save()
            logger.info(
                f"Workflow '{self.workflow.name}' for object '{self.object_id}' has been put on hold."
            )
            return True
        else:
            logger.warning(
                f"No on-hold status defined for current step '{self.current_step.name}'. "
                "Please define a WorkflowStepStatus with 'is_on_hold_status=True' for this step."
            )
            return False


    def resume_workflow(self):
        """
        Attempts to resume the workflow from an on-hold state by setting its current
        step status back to the default status for the current step.
        """
        if self.is_completed():
            logger.info(f"Cannot resume workflow '{self.workflow.name}' as it is completed.")
            return False

        if (
            not self.current_step_status
            or not self.current_step_status.is_on_hold_status
        ):
            logger.info(
                f"Workflow '{self.workflow.name}' is not currently on hold, cannot resume."
            )
            return False

        default_status = self.current_step.possible_statuses.filter(
            is_default_status=True
        ).first()
        if default_status:
            self.current_step_status = default_status
            self.save()
            logger.info(
                f"Workflow '{self.workflow.name}' for object '{self.object_id}' has been resumed."
            )
            return True
        else:
            logger.error(
                f"Default status not found for current step '{self.current_step.name}'. "
                "Cannot resume workflow. Please define a default status for this step."
            )
            return False
