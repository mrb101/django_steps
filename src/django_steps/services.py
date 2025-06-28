import logging

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .models import Workflow, WorkflowInstance

logger = logging.getLogger(__name__)


def start_workflow_instance(
    workflow_name: str, content_object
) -> WorkflowInstance | None:
    """
    Starts a new workflow instance for a given content object and workflow name.

    Args:
        workflow_name (str): The name of the Workflow to instantiate.
        content_object: The Django model instance for which the workflow is being started.

    Returns:
        WorkflowInstance: The newly created and started WorkflowInstance.
        None: If the workflow cannot be started (e.g., Workflow not found, no initial step).

    Raises:
        ValueError: If the content_object is not a saved Django model instance.
        Exception: For other unexpected errors during workflow instantiation.
    """
    if not hasattr(content_object, "pk") or content_object.pk is None:
        raise ValueError("content_object must be a saved Django model instance.")

    try:
        workflow = Workflow.objects.get(name=workflow_name)
        content_type = ContentType.objects.get_for_model(content_object)

        # Check if an active instance for this workflow already exists for this object
        existing_instance = WorkflowInstance.objects.filter(
            workflow=workflow,
            content_type=content_type,
            object_id=str(content_object.pk),
        ).first()

        # If an existing instance is found and it's not yet completed, return it.
        # This prevents duplicate active workflows for the same object.
        if existing_instance and not existing_instance.is_completed():
            logger.warning(
                f"An active workflow instance for '{workflow_name}' "
                f"already exists for {content_type.model} (ID: {content_object.pk}). "
                "Returning existing instance."
            )
            return existing_instance

        with transaction.atomic():
            workflow_instance = WorkflowInstance.objects.create(
                workflow=workflow,
                content_type=content_type,
                object_id=str(content_object.pk),
            )
            # Use the method defined on the WorkflowInstance model to handle step/status initialization
            success = workflow_instance.start_workflow()
            if not success:
                logger.error(f"Failed to start workflow '{workflow_name}' for {content_type.model} (ID: {content_object.pk}).")
                return None

            # Refresh the instance to ensure we have current data
            workflow_instance.refresh_from_db()
            logger.info(
                f"Workflow '{workflow_name}' started successfully for {content_type.model} (ID: {content_object.pk})."
            )
            return workflow_instance

    except Workflow.DoesNotExist:
        logger.error(f"Workflow '{workflow_name}' not found.")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred while starting workflow: {e}")
        raise  # Re-raise the exception after logging for debugging


def update_workflow_step_status(
    workflow_instance: WorkflowInstance, new_status_name: str, context_data: dict = None
) -> bool:
    """
    Updates the current step's status for a given workflow instance.
    If the new status is a completion status, it attempts to advance the workflow
    using the provided context_data for CEL evaluation.

    Args:
        workflow_instance (WorkflowInstance): The instance to update.
        new_status_name (str): The name of the new WorkflowStepStatus.
        context_data (dict, optional): Data to provide to CEL expressions for evaluation.
                                      If None, it will attempt to extract from content_object.

    Returns:
        bool: True if the status was updated and possibly advanced, False otherwise.
    """
    if not isinstance(workflow_instance, WorkflowInstance):
        raise TypeError("workflow_instance must be an instance of WorkflowInstance.")

    if workflow_instance.is_completed():
        logger.info(
            f"Cannot update status: Workflow '{workflow_instance.workflow.name}' is already completed."
        )
        return False

    with transaction.atomic():
        # Pass the context_data to the model method
        # The model's update_step_status method will then call _advance_to_next_workflow_step
        # which now accepts context_data
        success = workflow_instance.update_step_status(
            new_status_name, context_data=context_data
        )
        if success:
            logger.info(
                f"Workflow instance {workflow_instance.id} status updated to "
                f"'{workflow_instance.current_step_status.name}'."
            )
        else:
            logger.error(
                f"Failed to update workflow instance {workflow_instance.id} status to '{new_status_name}'."
            )
        return success


def cancel_workflow_instance(workflow_instance: WorkflowInstance) -> bool:
    """
    Attempts to cancel a workflow instance.

    Args:
        workflow_instance (WorkflowInstance): The instance to cancel.

    Returns:
        bool: True if the workflow was successfully cancelled, False otherwise.
    """
    if not isinstance(workflow_instance, WorkflowInstance):
        raise TypeError("workflow_instance must be an instance of WorkflowInstance.")

    with transaction.atomic():
        success = workflow_instance.cancel_workflow()
        if success:
            logger.info(f"Workflow instance {workflow_instance.id} has been cancelled.")
        else:
            logger.error(f"Failed to cancel workflow instance {workflow_instance.id}.")
        return success


def set_workflow_on_hold(workflow_instance: WorkflowInstance) -> bool:
    """
    Attempts to put a workflow instance on hold.

    Args:
        workflow_instance (WorkflowInstance): The instance to put on hold.

    Returns:
        bool: True if the workflow was successfully put on hold, False otherwise.
    """
    if not isinstance(workflow_instance, WorkflowInstance):
        raise TypeError("workflow_instance must be an instance of WorkflowInstance.")

    with transaction.atomic():
        success = workflow_instance.set_on_hold()
        if success:
            logger.info(f"Workflow instance {workflow_instance.id} has been put on hold.")
        else:
            logger.error(f"Failed to set workflow instance {workflow_instance.id} on hold.")
        return success


def resume_workflow_instance(workflow_instance: WorkflowInstance) -> bool:
    """
    Attempts to resume a workflow instance from an on-hold state.

    Args:
        workflow_instance (WorkflowInstance): The instance to resume.

    Returns:
        bool: True if the workflow was successfully resumed, False otherwise.
    """
    if not isinstance(workflow_instance, WorkflowInstance):
        raise TypeError("workflow_instance must be an instance of WorkflowInstance.")

    with transaction.atomic():
        success = workflow_instance.resume_workflow()
        if success:
            logger.info(f"Workflow instance {workflow_instance.id} has been resumed.")
        else:
            logger.error(f"Failed to resume workflow instance {workflow_instance.id}.")
        return success


def get_workflow_instance_for_object(
    content_object, workflow_name: str | None = None
) -> WorkflowInstance | None:
    """
    Retrieves a workflow instance associated with a given content object.
    Optionally filters by workflow name.

    Args:
        content_object: The Django model instance to query for.
        workflow_name (str, optional): The name of the specific workflow to find.

    Returns:
        WorkflowInstance: The found WorkflowInstance, or None if not found.
    """
    try:
        if not hasattr(content_object, "pk") or content_object.pk is None:
            logger.warning("Content_object has no pk attribute or pk is None")
            return None

        content_type = ContentType.objects.get_for_model(content_object)
        query = WorkflowInstance.objects.filter(
            content_type=content_type, object_id=str(content_object.pk)
        )
    except Exception as e:
        logger.error(f"Error getting workflow instance for object: {e}")
        return None

    if workflow_name:
        try:
            workflow = Workflow.objects.get(name=workflow_name)
            query = query.filter(workflow=workflow)
        except Workflow.DoesNotExist:
            logger.warning(
                f"Workflow '{workflow_name}' not found when querying for instance."
            )
            return None

    try:
        # Get the latest instance if multiple (e.g., if you allow re-starting workflows)
        # Or, refine logic to find the *active* instance based on your needs
        instance = query.order_by("-started_at").first()
        return instance
    except ObjectDoesNotExist:
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred while fetching workflow instance: {e}")
        return None
