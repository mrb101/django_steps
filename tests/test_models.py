import pytest
from django.db import IntegrityError, transaction

from django_steps.models import (
    Workflow, WorkflowInstance, WorkflowStep, WorkflowStepStatus, WorkflowTransition
)


@pytest.mark.django_db
class TestWorkflowModels:
    """Tests for the basic model functionality and properties"""

    def test_workflow_creation(self, workflow_data):
        """Test the basic creation and string representation of Workflow model."""
        workflows = Workflow.objects.all()
        assert workflows.count() >= 2  # At least our test workflows
        assert str(workflow_data["workflow_investigation"]) == "Investigation Workflow"

    def test_workflow_step_creation(self, workflow_data):
        """Test the creation and properties of WorkflowStep model."""
        workflow = workflow_data["workflow_investigation"]
        step_init = workflow_data["step_int_1_init"]
        step_final = workflow_data["step_int_5_report"]

        assert workflow.steps.count() == 5
        assert step_init.name == "Initial Review"
        assert step_init.is_initial_step is True
        assert step_init.is_final_step is False
        assert step_final.is_final_step is True

    def test_workflow_step_status_creation(self, workflow_data):
        """Test the creation and properties of WorkflowStepStatus model."""
        step = workflow_data["step_int_1_init"]
        default_status = workflow_data["status_int_1_default"]
        complete_status = workflow_data["status_int_1_complete"]
        on_hold_status = workflow_data["status_int_1_on_hold"]
        cancel_status = workflow_data["status_int_1_cancelled"]

        assert step.possible_statuses.count() == 5
        assert default_status.is_default_status is True
        assert default_status.is_completion_status is False
        assert complete_status.is_completion_status is True
        assert on_hold_status.is_on_hold_status is True
        assert cancel_status.is_cancellation_status is True
        assert cancel_status.is_completion_status is True  # Cancellation can also be completion

    def test_workflow_transition_creation(self, workflow_data):
        """Test the creation and properties of WorkflowTransition model."""
        total_transitions = WorkflowTransition.objects.count()
        assert total_transitions >= 7  # At least the transitions from our fixture

        from_step = workflow_data["step_int_1_init"]
        to_step = workflow_data["step_int_3_interview"]

        transition = WorkflowTransition.objects.get(
            from_step=from_step, 
            to_step=to_step
        )
        assert transition.condition == "claim.is_high_risk == true"
        assert transition.priority == 20
        assert str(transition) == "Transition from 'Initial Review' to 'Interview Stakeholders' (Investigation Workflow)"

    def test_workflow_instance_creation(self, workflow_data):
        """Test the basic creation and initialization of WorkflowInstance for User model."""
        # Test the pre-created instances from the fixture
        instance_low_risk = workflow_data["instance_low_risk"]
        instance_high_risk = workflow_data["instance_high_risk"]
        instance_cancelled = workflow_data["instance_cancelled"]

        # Verify the instances were created correctly
        assert instance_low_risk.id is not None
        assert instance_high_risk.id is not None
        assert instance_cancelled.id is not None

        # Verify the workflows were assigned correctly
        assert instance_low_risk.workflow == workflow_data["workflow_investigation"]
        assert instance_high_risk.workflow == workflow_data["workflow_investigation"]
        assert instance_cancelled.workflow == workflow_data["workflow_fasttrack"]

        # Verify the content_objects are the User instances
        assert instance_low_risk.content_object == workflow_data["test_users"]["low_risk"]
        assert instance_high_risk.content_object == workflow_data["test_users"]["high_risk"]
        assert instance_cancelled.content_object == workflow_data["test_users"]["cancelled"]

        # Verify the workflows were initialized
        assert instance_low_risk.current_step is not None
        assert instance_high_risk.current_step is not None
        assert instance_cancelled.current_step is not None

        # Verify the initial steps are correct
        assert instance_low_risk.current_step.is_initial_step is True
        assert instance_high_risk.current_step.is_initial_step is True
        assert instance_cancelled.current_step.is_initial_step is True

        # Verify the initial statuses are the default statuses
        assert instance_low_risk.current_step_status.is_default_status is True
        assert instance_high_risk.current_step_status.is_default_status is True
        assert instance_cancelled.current_step_status.is_default_status is True

        # Verify the workflows are not completed
        assert instance_low_risk.completed_at is None
        assert instance_high_risk.completed_at is None
        assert instance_cancelled.completed_at is None
        assert instance_low_risk.is_completed() is False
        assert instance_high_risk.is_completed() is False
        assert instance_cancelled.is_completed() is False


@pytest.mark.django_db
class TestWorkflowValidation:
    """Tests for model validation constraints"""

    def test_workflow_step_status_unique_default_validation(self, workflow_data):
        """Test that a WorkflowStep can only have one default status."""
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                WorkflowStepStatus.objects.create(
                    step=workflow_data["step_int_1_init"],
                    name="Another Default Dupe",
                    is_default_status=True,
                )

    def test_workflow_step_status_unique_cancellation_validation(self, workflow_data):
        """Test that a WorkflowStep can only have one cancellation status."""
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                WorkflowStepStatus.objects.create(
                    step=workflow_data["step_int_1_init"],
                    name="Another Cancelled Dupe",
                    is_cancellation_status=True,
                )

    def test_workflow_step_status_unique_on_hold_validation(self, workflow_data):
        """Test that a WorkflowStep can only have one on-hold status."""
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                WorkflowStepStatus.objects.create(
                    step=workflow_data["step_int_1_init"],
                    name="Another On Hold Dupe",
                    is_on_hold_status=True,
                )

    def test_workflow_step_unique_order_per_workflow(self, workflow_data):
        """Test that WorkflowStep orders are unique within a workflow."""
        with transaction.atomic():
            with pytest.raises(IntegrityError):  # Hits unique_together constraint
                WorkflowStep.objects.create(
                    workflow=workflow_data["workflow_investigation"],
                    name="Duplicate Order Step",
                    order=1,  # Duplicates existing step's order
                )

    def test_workflow_transition_unique_priority_per_from_to_step(self, workflow_data):
        """Test that WorkflowTransition priorities are unique for a given from_step to to_step pair."""
        with transaction.atomic():
            with pytest.raises(IntegrityError):  # Hits unique_together constraint
                WorkflowTransition.objects.create(
                    workflow=workflow_data["workflow_investigation"],
                    from_step=workflow_data["step_int_1_init"],
                    to_step=workflow_data["step_int_3_interview"],
                    condition="claim.amount == 123",  # Condition here is different, but priority is same
                    priority=20,  # Duplicates existing priority for this from/to pair
                )
