import uuid
import pytest

from django_steps.services import (
    start_workflow_instance,
    update_workflow_step_status,
    cancel_workflow_instance,
    set_workflow_on_hold,
    resume_workflow_instance,
    get_workflow_instance_for_object
)


@pytest.mark.django_db
class TestWorkflowServices:
    """Tests for the service layer functions"""

    def test_service_start_workflow_instance_success(self, workflow_data, test_users):
        """Test the service function for starting a workflow instance."""
        test_obj = test_users["another"]
        instance = start_workflow_instance(
            workflow_data["workflow_investigation"].name,
            test_obj
        )
        assert instance is not None
        assert instance.workflow == workflow_data["workflow_investigation"]
        assert instance.content_object == test_users["another"]
        assert instance.current_step == workflow_data["step_int_1_init"]
        assert instance.current_step_status == workflow_data["status_int_1_default"]

    def test_service_start_workflow_instance_invalid_object(self):
        """Test service function handles unsaved content_object."""
        with pytest.raises(ValueError):
            start_workflow_instance("Any Workflow", {})  # Pass a dict to simulate unsaved object

    def test_service_start_workflow_instance_not_found(self, test_users, workflow_data):
        """Test service function when workflow name does not exist."""
        test_obj = test_users["another"]
        instance = start_workflow_instance("NonExistentWorkflow", test_obj)
        assert instance is None

    def test_service_start_workflow_instance_duplicate_active(self, workflow_data, test_users):
        """Test service function returns existing active instance to prevent duplicates."""
        test_obj = test_users["another"]

        # Start first instance
        first_instance = start_workflow_instance(
            workflow_data["workflow_investigation"].name, test_obj
        )
        assert first_instance is not None

        # Try to start again for the same object and workflow
        second_instance = start_workflow_instance(
            workflow_data["workflow_investigation"].name, test_obj
        )
        assert first_instance.id == second_instance.id  # Should return the same instance

    def test_service_update_workflow_step_status_success(self, workflow_data, test_users):
        """Test the service function for updating step status."""
        test_obj = test_users["another"]

        instance = start_workflow_instance(workflow_data["workflow_fasttrack"].name, test_obj)
        assert instance is not None

        # Update status, which should trigger advancement
        # 'claim.status_field == "Approved"' for transition to step_ft_2_approve
        result = update_workflow_step_status(
            instance,
            "Check Passed",
            context_data={"claim": {"status_field": "Approved"}},
        )
        assert result is True

        instance.refresh_from_db()
        assert instance.current_step == workflow_data["step_ft_2_approve"]
        assert instance.current_step_status == workflow_data["status_ft_2_default"]

    def test_service_cancel_workflow_instance(self, workflow_data, test_users):
        """Test the service function for cancelling a workflow."""
        test_obj = test_users["another"]
        instance = start_workflow_instance(workflow_data["workflow_investigation"].name, test_obj)
        assert instance is not None

        # Ensure the current step has a cancellation status defined for this test
        # (Already done in fixture for step_int_1_init)
        assert cancel_workflow_instance(instance) is True
        instance.refresh_from_db()
        assert instance.current_step_status.is_cancellation_status is True
        assert instance.is_completed() is True

    def test_service_set_workflow_on_hold(self, workflow_data, test_users):
        """Test the service function for putting a workflow on hold."""
        test_obj = test_users["another"]
        instance = start_workflow_instance(workflow_data["workflow_investigation"].name, test_obj)
        assert instance is not None

        assert set_workflow_on_hold(instance) is True
        instance.refresh_from_db()
        assert instance.current_step_status.is_on_hold_status is True

    def test_service_resume_workflow_instance(self, workflow_data, test_users):
        """Test the service function for resuming a workflow."""
        test_obj = test_users["another"]
        instance = start_workflow_instance(workflow_data["workflow_investigation"].name, test_obj)
        assert instance is not None

        set_workflow_on_hold(instance)  # Put on hold first
        assert resume_workflow_instance(instance) is True
        instance.refresh_from_db()
        assert instance.current_step_status.is_on_hold_status is False
        assert instance.current_step_status.is_default_status is True

    def test_service_get_workflow_instance_for_object(self, workflow_data, test_users):
        """Test the service function for retrieving workflow instances."""
        test_obj = test_users["another"]

        # Create instances using this object
        instance_1 = start_workflow_instance(
            workflow_data["workflow_investigation"].name, test_obj
        )
        # To get a second instance for the same object, it must be a different workflow type
        instance_2 = start_workflow_instance(
            workflow_data["workflow_fasttrack"].name, test_obj
        )

        # Test specific workflow retrieval
        retrieved_investigation = get_workflow_instance_for_object(
            test_obj, workflow_name=workflow_data["workflow_investigation"].name
        )
        assert retrieved_investigation == instance_1

        retrieved_fasttrack = get_workflow_instance_for_object(
            test_obj, workflow_name=workflow_data["workflow_fasttrack"].name
        )
        assert retrieved_fasttrack == instance_2

        # Test retrieval without specifying workflow_name (should get the most recent)
        retrieved_any = get_workflow_instance_for_object(test_obj)
        assert retrieved_any == instance_2  # instance_2 was created later

        # Test no instance found for a non-existent object
        class MockUnsavedObject:  # Simple mock for a non-existent object
            pk = str(uuid.uuid4())

        mock_obj = MockUnsavedObject()
        no_instance = get_workflow_instance_for_object(mock_obj)
        assert no_instance is None

        # Test no instance found for specific workflow name
        no_instance_specific = get_workflow_instance_for_object(
            test_obj, workflow_name="AnotherNonExistentWorkflow"
        )
        assert no_instance_specific is None
