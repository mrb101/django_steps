import datetime
import pytest

from django_steps.models import (
    Workflow, WorkflowInstance, WorkflowStep, WorkflowStepStatus, WorkflowTransition
)


@pytest.mark.django_db
class TestWorkflowInstanceOperations:
    """Tests for workflow instance operations (start, update, advance, etc.)"""

    def test_start_workflow_success(self, workflow_data, test_users):
        """Test successful initialization of a WorkflowInstance."""
        # Create a new instance for the test_users["another"] user
        instance = WorkflowInstance.objects.create(
            workflow=workflow_data["workflow_investigation"],
            content_type=workflow_data["generic_content_type"],
            object_id=test_users["another"].id,
        )
        assert instance.start_workflow() is True

        # Refresh from DB
        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_int_1_init"]
        assert instance.current_step_status == workflow_data["status_int_1_default"]
        assert instance.started_at is not None
        assert instance.is_completed() is False

        # Verify the content_object is the User instance
        assert instance.content_object == test_users["another"]

    def test_start_workflow_already_started(self, workflow_data):
        """Test that start_workflow does nothing if already started."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_low_risk"]

        # Save state
        initial_step = instance.current_step
        initial_status = instance.current_step_status

        # Try to start again
        assert instance.start_workflow() is False  # Should return False
        instance.refresh_from_db()
        assert instance.current_step == initial_step  # Should not change
        assert instance.current_step_status == initial_status  # Should not change

    def test_start_workflow_no_initial_step(self, workflow_data, test_users):
        """Test start_workflow fails if the workflow has no initial step."""
        workflow_no_init = Workflow.objects.create(name="No Initial Step Workflow")
        # No steps added, so no initial step
        instance = WorkflowInstance.objects.create(
            workflow=workflow_no_init,
            content_type=workflow_data["generic_content_type"],
            object_id=test_users["another"].id,
        )
        assert instance.start_workflow() is False
        instance.refresh_from_db()
        assert instance.current_step is None
        assert instance.current_step_status is None

    def test_start_workflow_no_default_status(self, workflow_data, test_users):
        """Test start_workflow fails if the initial step has no default status."""
        workflow_no_default_status = Workflow.objects.create(
            name="No Default Status Workflow"
        )
        step = WorkflowStep.objects.create(
            workflow=workflow_no_default_status,
            name="Only Non-Default",
            order=1,
            is_initial_step=True,
        )
        WorkflowStepStatus.objects.create(step=step, name="Just a status")  # No default

        instance = WorkflowInstance.objects.create(
            workflow=workflow_no_default_status,
            content_type=workflow_data["generic_content_type"],
            object_id=test_users["another"].id,
        )
        assert instance.start_workflow() is False
        instance.refresh_from_db()
        assert instance.current_step is None
        assert instance.current_step_status is None

    def test_update_step_status_success_no_advance(self, workflow_data):
        """Test updating a step status without triggering advancement."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_low_risk"]

        # Update to a non-completion status
        assert instance.update_step_status("Assigned") is True
        instance.refresh_from_db()
        assert instance.current_step_status == workflow_data["status_int_1_assigned"]
        assert instance.current_step == workflow_data["step_int_1_init"]  # Should not have advanced

    def test_update_step_status_invalid_status_name(self, workflow_data):
        """Test updating a step status with an invalid status name for the current step."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_low_risk"]

        # Try to set a status that doesn't exist for this step
        assert instance.update_step_status("NonExistentStatus") is False
        instance.refresh_from_db()
        assert instance.current_step_status == workflow_data["status_int_1_default"]  # Should not have changed

    def test_advance_workflow_unconditional_transition(self, workflow_data):
        """Test workflow advancement via an unconditional transition (empty CEL condition)."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_low_risk"]

        # Trigger advancement by completing the current step with appropriate context
        # Condition "claim.is_high_risk == false" for step_int_1_init -> step_int_2_doc_collection (priority 10)
        assert instance.update_step_status(
            "Review Complete", context_data={"claim": {"is_high_risk": False}}
        ) is True
        instance.refresh_from_db()

        assert instance.current_step == workflow_data["step_int_2_doc_collection"]  # Should advance
        assert instance.current_step_status == workflow_data["status_int_2_default"]  # Should be default of next step

        # From Document Collection to Final Report (unconditional transition)
        assert instance.update_step_status("Docs Complete", context_data={"claim": {}}) is True
        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_int_5_report"]
        assert instance.current_step_status == workflow_data["status_int_5_default"]
        assert instance.is_completed() is False  # Not completed until final status on final step

    def test_advance_workflow_conditional_transition_true(self, workflow_data):
        """Test workflow advancement via a conditional transition that evaluates to true."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_high_risk"]

        # Update status, providing context data that makes the 'is_high_risk == true' condition true
        assert instance.update_step_status(
            "Review Complete", context_data={"claim": {"is_high_risk": True}}
        ) is True
        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_int_3_interview"]  # Should go to Interview Stakeholders
        assert instance.current_step_status.name == "Pending Assignment"  # Default status for step_int_3_interview

    def test_advance_workflow_conditional_transitions(self, workflow_data, test_users):
        """Test different transition cases based on conditions."""
        # Create a new instance for this test
        instance = WorkflowInstance.objects.create(
            workflow=workflow_data["workflow_investigation"],
            content_type=workflow_data["generic_content_type"],
            object_id=test_users["another"].id,
        )
        instance.start_workflow()

        # Manually set current step to step_int_3_interview for testing a specific transition scenario
        instance.current_step = workflow_data["step_int_3_interview"]
        instance.current_step_status = workflow_data["step_int_3_interview"].possible_statuses.filter(
            is_default_status=True
        ).first()
        instance.save()

        # Test transition from Interview Stakeholders with low amount
        assert instance.update_step_status(
            "Interview Complete", context_data={"claim": {"amount": 5000}}
        ) is True
        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_int_5_report"]  # Should go to Final Report
        assert instance.current_step_status == workflow_data["status_int_5_default"]

        # Let's create a scenario where NO transition matches from a custom step
        step_no_match = WorkflowStep.objects.create(
            workflow=workflow_data["workflow_investigation"],
            name="No Match Step",
            order=10,  # Ensure unique order
        )
        # Create default and completion statuses for this step
        status_no_match = WorkflowStepStatus.objects.create(
            step=step_no_match,
            name="Ready",
            is_default_status=True,
            is_completion_status=True,
        )
        # Create a dummy transition that always evaluates to false
        WorkflowTransition.objects.create(
            workflow=workflow_data["workflow_investigation"],
            from_step=step_no_match,
            to_step=workflow_data["step_int_5_report"],
            condition="false",  # Always false
            priority=1,
        )

        instance.current_step = step_no_match
        instance.current_step_status = status_no_match
        instance.save()

        # Try to advance, but no condition should be met
        assert instance.update_step_status("Ready", context_data={"claim": {}}) is False
        instance.refresh_from_db()
        assert instance.current_step == step_no_match  # Should remain on the same step

    def test_advance_workflow_priority(self, workflow_data):
        """Test that transitions with higher priority are evaluated first and taken."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_high_risk"]

        # We'll provide context where claim.is_high_risk is true, so Interview Stakeholders (priority 20) should be taken.
        assert instance.update_step_status(
            "Review Complete", context_data={"claim": {"is_high_risk": True}}
        ) is True
        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_int_3_interview"]

        # Test another priority case from step_int_3_interview
        instance.current_step = workflow_data["step_int_3_interview"]
        instance.current_step_status = workflow_data["step_int_3_interview"].possible_statuses.filter(
            is_default_status=True
        ).first()
        instance.save()

        # Set amount to 20000 (high), should go to Inspection (priority 10)
        assert instance.update_step_status(
            "Interview Complete", context_data={"claim": {"amount": 20000}}
        ) is True
        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_int_4_inspection"]  # Should go to Schedule Inspection

    def test_advance_workflow_reaches_final_step(self, workflow_data, test_users):
        """Test that workflow is marked completed when it reaches the final step and its completion status."""
        # Create a new instance for this test
        instance = WorkflowInstance.objects.create(
            workflow=workflow_data["workflow_investigation"],
            content_type=workflow_data["generic_content_type"],
            object_id=test_users["another"].id,
        )
        instance.start_workflow()

        # Advance to Document Collection (unconditional transition with high_risk=False context)
        assert instance.update_step_status(
            "Review Complete", context_data={"claim": {"is_high_risk": False}}
        ) is True
        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_int_2_doc_collection"]

        # Complete Document Collection, should go directly to Final Report (unconditional transition)
        assert instance.update_step_status("Docs Complete", context_data={"claim": {}}) is True
        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_int_5_report"]  # Now on final step
        assert instance.is_completed() is False  # Not completed yet, still needs final step's completion status

        # Set final step status to completion status
        assert instance.update_step_status("Report Approved") is True
        instance.refresh_from_db()
        assert instance.is_completed() is True
        assert instance.completed_at is not None
        assert instance.current_step_status == workflow_data["status_int_5_final_approved"]

    def test_cancel_workflow_instance_success(self, workflow_data):
        """Test successful cancellation of a workflow instance."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_cancelled"]

        assert instance.current_step_status.is_cancellation_status is False
        assert instance.cancel_workflow() is True
        instance.refresh_from_db()
        assert instance.current_step_status.is_cancellation_status is True
        assert instance.completed_at is not None
        print(instance.current_step, instance.current_step.is_final_step, instance.current_step_status,
              instance.current_step_status.is_completion_status)
        assert instance.is_completed() is True  # A cancelled workflow is considered completed

    def test_cancel_workflow_instance_already_completed(self, workflow_data, test_users):
        """Test that a completed workflow cannot be cancelled again."""
        # Create a new instance for this test
        instance = WorkflowInstance.objects.create(
            workflow=workflow_data["workflow_investigation"],
            content_type=workflow_data["generic_content_type"],
            object_id=test_users["another"].id,
        )
        instance.start_workflow()
        instance.current_step = workflow_data["step_int_5_report"]  # Set to final step
        instance.current_step_status = workflow_data["status_int_5_final_approved"]  # Set to completion status
        instance.completed_at = datetime.datetime.now()
        instance.save()
        assert instance.is_completed() is True

        assert instance.cancel_workflow() is False  # Should not be able to cancel
        instance.refresh_from_db()
        assert instance.current_step_status.is_cancellation_status is False  # Status should not have changed

    def test_set_workflow_on_hold_success(self, workflow_data):
        """Test successful setting of workflow instance to on-hold."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_low_risk"]

        assert instance.current_step_status.is_on_hold_status is False
        assert instance.set_on_hold() is True
        instance.refresh_from_db()
        assert instance.current_step_status.is_on_hold_status is True
        assert instance.is_completed() is False  # On hold is not completed

    def test_set_workflow_on_hold_already_on_hold(self, workflow_data, test_users):
        """Test that an already on-hold workflow cannot be set on hold again."""
        # Create a new instance for this test
        instance = WorkflowInstance.objects.create(
            workflow=workflow_data["workflow_investigation"],
            content_type=workflow_data["generic_content_type"],
            object_id=test_users["another"].id,
        )
        instance.start_workflow()
        instance.set_on_hold()  # First set on hold

        assert instance.current_step_status.is_on_hold_status is True
        assert instance.set_on_hold() is False  # Should return False
        instance.refresh_from_db()
        assert instance.current_step_status.is_on_hold_status is True  # Status should not change

    def test_resume_workflow_instance_success(self, workflow_data, test_users):
        """Test successful resumption of a workflow instance from on-hold."""
        # Create a new instance for this test
        instance = WorkflowInstance.objects.create(
            workflow=workflow_data["workflow_investigation"],
            content_type=workflow_data["generic_content_type"],
            object_id=test_users["another"].id,
        )
        instance.start_workflow()
        instance.set_on_hold()  # Put on hold first

        assert instance.current_step_status.is_on_hold_status is True
        assert instance.resume_workflow() is True
        instance.refresh_from_db()
        assert instance.current_step_status.is_on_hold_status is False
        assert instance.current_step_status.is_default_status is True  # Should revert to default status

    def test_resume_workflow_instance_not_on_hold(self, workflow_data):
        """Test that a non-on-hold workflow cannot be resumed."""
        # Use the pre-initialized instance from the fixture
        instance = workflow_data["instance_low_risk"]

        assert instance.current_step_status.is_on_hold_status is False
        assert instance.resume_workflow() is False  # Should return False
        instance.refresh_from_db()
        assert instance.current_step_status.is_on_hold_status is False  # Status should not change
