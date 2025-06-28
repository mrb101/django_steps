import uuid
import pytest  # noqa
from django.conf import settings
import pytest

# Import these after Django is configured
# from django.contrib.contenttypes.models import ContentType
# from src.django_steps.models import (
#     Workflow, WorkflowStep,
#     WorkflowStepStatus, WorkflowTransition
# )


def pytest_configure():
    """
    Configure Django settings for tests
    """
    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sites",
            "django.contrib.admin",
            "django_steps",
        ],
        SITE_ID=1,
        MIDDLEWARE=[],
        ROOT_URLCONF="tests.urls",
        SECRET_KEY="test-key",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            },
        ],
    )

    import django

    django.setup()



@pytest.fixture(scope="session")
def django_db_setup(django_db_setup):
    """Ensure database is set up for tests"""
    pass


@pytest.fixture
def generic_content_type():
    """Return a ContentType for the User model"""
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import User
    return ContentType.objects.get_for_model(User)


@pytest.fixture
def test_users():
    """Create test users for workflow testing"""
    from django.contrib.auth.models import User

    # Create test users with different characteristics
    user_low_risk = User.objects.create_user(
        username="user_low_risk",
        email="low_risk@example.com",
        password="password123"
    )

    user_high_risk = User.objects.create_user(
        username="user_high_risk",
        email="high_risk@example.com",
        password="password123"
    )

    user_cancelled = User.objects.create_user(
        username="user_cancelled",
        email="cancelled@example.com",
        password="password123"
    )

    user_another = User.objects.create_user(
        username="user_another",
        email="another@example.com",
        password="password123"
    )

    return {
        "low_risk": user_low_risk,
        "high_risk": user_high_risk,
        "cancelled": user_cancelled,
        "another": user_another
    }

@pytest.fixture
def test_uuids():
    """Generate unique UUIDs for test objects"""
    return {
        "low_risk": str(uuid.uuid4()),
        "high_risk": str(uuid.uuid4()),
        "cancelled": str(uuid.uuid4()),
        "another": str(uuid.uuid4())
    }


@pytest.fixture
def workflow_data(generic_content_type, test_users):
    """Create workflows, steps, statuses and transitions for testing"""
    from django_steps.models import Workflow, WorkflowStep, WorkflowStepStatus, WorkflowTransition

    # 1. Create Workflows
    workflow_investigation = Workflow.objects.create(
        name="Investigation Workflow", description="Detailed investigation process."
    )
    workflow_fasttrack = Workflow.objects.create(
        name="Fast-Track Workflow",
        description="Expedited process for simple cases.",
    )

    # 2. Create Workflow Steps for Investigation Workflow
    step_int_1_init = WorkflowStep.objects.create(
        workflow=workflow_investigation,
        name="Initial Review",
        order=1,
        is_initial_step=True,
    )
    step_int_2_doc_collection = WorkflowStep.objects.create(
        workflow=workflow_investigation, name="Document Collection", order=2
    )
    step_int_3_interview = WorkflowStep.objects.create(
        workflow=workflow_investigation, name="Interview Stakeholders", order=3
    )
    step_int_4_inspection = WorkflowStep.objects.create(
        workflow=workflow_investigation, name="Schedule Inspection", order=4
    )
    step_int_5_report = WorkflowStep.objects.create(
        workflow=workflow_investigation,
        name="Final Report",
        order=5,
        is_final_step=True,
    )

    # 3. Create Workflow Steps for Fast-Track Workflow
    step_ft_1_init = WorkflowStep.objects.create(
        workflow=workflow_fasttrack,
        name="Initial Check",
        order=1,
        is_initial_step=True,
    )
    step_ft_2_approve = WorkflowStep.objects.create(
        workflow=workflow_fasttrack, name="Approve", order=2, is_final_step=True
    )
    step_ft_3_reject = WorkflowStep.objects.create(
        workflow=workflow_fasttrack, name="Reject", order=3, is_final_step=True
    )

    # 4. Create Workflow Step Statuses for Investigation Workflow steps
    # Statuses for Initial Review (step_int_1_init)
    status_int_1_default = WorkflowStepStatus.objects.create(
        step=step_int_1_init, name="Pending Assignment", is_default_status=True
    )
    status_int_1_assigned = WorkflowStepStatus.objects.create(
        step=step_int_1_init, name="Assigned"
    )
    status_int_1_complete = WorkflowStepStatus.objects.create(
        step=step_int_1_init, name="Review Complete", is_completion_status=True
    )
    status_int_1_on_hold = WorkflowStepStatus.objects.create(
        step=step_int_1_init, name="Review On Hold", is_on_hold_status=True
    )
    status_int_1_cancelled = WorkflowStepStatus.objects.create(
        step=step_int_1_init,
        name="Review Cancelled",
        is_cancellation_status=True,
        is_completion_status=True,
    )

    # Statuses for Document Collection (step_int_2_doc_collection)
    status_int_2_default = WorkflowStepStatus.objects.create(
        step=step_int_2_doc_collection,
        name="Awaiting Docs",
        is_default_status=True,
    )
    status_int_2_partial = WorkflowStepStatus.objects.create(
        step=step_int_2_doc_collection, name="Partial Docs"
    )
    status_int_2_complete = WorkflowStepStatus.objects.create(
        step=step_int_2_doc_collection,
        name="Docs Complete",
        is_completion_status=True,
    )

    # Statuses for Interview Stakeholders (step_int_3_interview)
    status_int_3_default = WorkflowStepStatus.objects.create(
        step=step_int_3_interview,
        name="Pending Assignment",
        is_default_status=True,
    )
    status_int_3_complete = WorkflowStepStatus.objects.create(
        step=step_int_3_interview,
        name="Interview Complete",
        is_completion_status=True,
    )

    # Statuses for Schedule Inspection (step_int_4_inspection)
    status_int_4_default = WorkflowStepStatus.objects.create(
        step=step_int_4_inspection,
        name="Scheduling",
        is_default_status=True,
    )
    status_int_4_complete = WorkflowStepStatus.objects.create(
        step=step_int_4_inspection,
        name="Inspection Complete",
        is_completion_status=True,
    )

    # Statuses for Final Report (step_int_5_report) - a final step
    status_int_5_default = WorkflowStepStatus.objects.create(
        step=step_int_5_report, name="Drafting Report", is_default_status=True
    )
    status_int_5_final_approved = WorkflowStepStatus.objects.create(
        step=step_int_5_report,
        name="Report Approved",
        is_completion_status=True,
    )
    status_int_5_final_rejected = WorkflowStepStatus.objects.create(
        step=step_int_5_report,
        name="Report Rejected",
        is_completion_status=True,
    )

    # 5. Create Workflow Step Statuses for Fast-Track Workflow steps
    # Statuses for Initial Check (step_ft_1_init)
    status_ft_1_default = WorkflowStepStatus.objects.create(
        step=step_ft_1_init, name="Ready for Check", is_default_status=True
    )
    status_ft_1_pass = WorkflowStepStatus.objects.create(
        step=step_ft_1_init, name="Check Passed", is_completion_status=True
    )
    status_ft_1_fail = WorkflowStepStatus.objects.create(
        step=step_ft_1_init, name="Check Failed", is_completion_status=True
    )

    # Statuses for Approve (step_ft_2_approve) - a final step
    status_ft_2_default = WorkflowStepStatus.objects.create(
        step=step_ft_2_approve, name="Pending Approval", is_default_status=True
    )
    status_ft_2_approved = WorkflowStepStatus.objects.create(
        step=step_ft_2_approve, name="Approved Final", is_completion_status=True
    )

    # Statuses for Reject (step_ft_3_reject) - a final step
    status_ft_3_default = WorkflowStepStatus.objects.create(
        step=step_ft_3_reject, name="Pending Rejection", is_default_status=True
    )
    status_ft_3_rejected = WorkflowStepStatus.objects.create(
        step=step_ft_3_reject, name="Rejected Final", is_completion_status=True
    )

    # 6. Create Workflow Transitions for Investigation Workflow
    # From Initial Review (step_int_1_init)
    # Note: 'claim' in conditions will refer to a dictionary passed in context_data
    WorkflowTransition.objects.create(
        workflow=workflow_investigation,
        from_step=step_int_1_init,
        to_step=step_int_2_doc_collection,
        condition="claim.is_high_risk == false",  # Condition for low risk claims
        priority=10,
        description="Proceed to Document Collection for low risk claims.",
    )
    WorkflowTransition.objects.create(
        workflow=workflow_investigation,
        from_step=step_int_1_init,
        to_step=step_int_3_interview,
        condition="claim.is_high_risk == true",  # Condition for high risk claims
        priority=20,  # Higher priority, evaluated first
        description="Proceed to Interview Stakeholders for high risk claims.",
    )

    # From Document Collection (step_int_2_doc_collection) - unconditional
    WorkflowTransition.objects.create(
        workflow=workflow_investigation,
        from_step=step_int_2_doc_collection,
        to_step=step_int_5_report,  # Skip interview/inspection for simple cases
        condition="",  # Unconditional
        priority=0,
        description="Proceed directly to Final Report after document collection (unconditional).",
    )

    # From Interview Stakeholders (step_int_3_interview) - conditional based on amount
    WorkflowTransition.objects.create(
        workflow=workflow_investigation,
        from_step=step_int_3_interview,
        to_step=step_int_4_inspection,
        condition="claim.amount > 10000",
        priority=10,
        description="Proceed to Inspection if amount is high after interview.",
    )
    WorkflowTransition.objects.create(
        workflow=workflow_investigation,
        from_step=step_int_3_interview,
        to_step=step_int_5_report,
        condition="claim.amount <= 10000",
        priority=5,
        description="Proceed to Final Report if amount is low after interview.",
    )

    # From Schedule Inspection (step_int_4_inspection) - unconditional to final report
    WorkflowTransition.objects.create(
        workflow=workflow_investigation,
        from_step=step_int_4_inspection,
        to_step=step_int_5_report,
        condition="",
        priority=0,
        description="Proceed to Final Report after inspection.",
    )

    # 7. Create Workflow Transitions for Fast-Track Workflow
    # From Initial Check (step_ft_1_init)
    WorkflowTransition.objects.create(
        workflow=workflow_fasttrack,
        from_step=step_ft_1_init,
        to_step=step_ft_2_approve,
        condition='claim.status_field == "Approved"',  # Example for fast-track approval
        priority=10,
        description="Approve fast-track if status is approved.",
    )
    WorkflowTransition.objects.create(
        workflow=workflow_fasttrack,
        from_step=step_ft_1_init,
        to_step=step_ft_3_reject,
        condition='claim.status_field == "Rejected"',  # Example for fast-track rejection
        priority=5,
        description="Reject fast-track if status is rejected.",
    )

    # 8. Create Workflow Instances for test users
    from django_steps.models import WorkflowInstance

    # Create workflow instances for users
    instance_low_risk = WorkflowInstance.objects.create(
        workflow=workflow_investigation,
        content_type=generic_content_type,
        object_id=test_users["low_risk"].id,
    )

    instance_high_risk = WorkflowInstance.objects.create(
        workflow=workflow_investigation,
        content_type=generic_content_type,
        object_id=test_users["high_risk"].id,
    )

    instance_cancelled = WorkflowInstance.objects.create(
        workflow=workflow_fasttrack,
        content_type=generic_content_type,
        object_id=test_users["cancelled"].id,
    )

    # Initialize the workflow for the low_risk user
    instance_low_risk.start_workflow()

    # Initialize the workflow for the high_risk user
    instance_high_risk.start_workflow()

    # Initialize the workflow for the cancelled user
    instance_cancelled.start_workflow()

    # Return a dictionary with all the created objects
    return {
        "workflow_investigation": workflow_investigation,
        "workflow_fasttrack": workflow_fasttrack,
        "step_int_1_init": step_int_1_init,
        "step_int_2_doc_collection": step_int_2_doc_collection,
        "step_int_3_interview": step_int_3_interview,
        "step_int_4_inspection": step_int_4_inspection,
        "step_int_5_report": step_int_5_report,
        "step_ft_1_init": step_ft_1_init,
        "step_ft_2_approve": step_ft_2_approve,
        "step_ft_3_reject": step_ft_3_reject,
        "status_int_1_default": status_int_1_default,
        "status_int_1_assigned": status_int_1_assigned,
        "status_int_1_complete": status_int_1_complete,
        "status_int_1_on_hold": status_int_1_on_hold,
        "status_int_1_cancelled": status_int_1_cancelled,
        "status_int_2_default": status_int_2_default,
        "status_int_2_partial": status_int_2_partial,
        "status_int_2_complete": status_int_2_complete,
        "status_int_3_default": status_int_3_default,
        "status_int_3_complete": status_int_3_complete,
        "status_int_4_default": status_int_4_default,
        "status_int_4_complete": status_int_4_complete,
        "status_int_5_default": status_int_5_default,
        "status_int_5_final_approved": status_int_5_final_approved,
        "status_int_5_final_rejected": status_int_5_final_rejected,
        "status_ft_1_default": status_ft_1_default,
        "status_ft_1_pass": status_ft_1_pass,
        "status_ft_1_fail": status_ft_1_fail,
        "status_ft_2_default": status_ft_2_default,
        "status_ft_2_approved": status_ft_2_approved,
        "status_ft_3_default": status_ft_3_default,
        "status_ft_3_rejected": status_ft_3_rejected,
        "instance_low_risk": instance_low_risk,
        "instance_high_risk": instance_high_risk,
        "instance_cancelled": instance_cancelled,
        "test_users": test_users,
        "generic_content_type": generic_content_type
    }
