from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_steps.models import Workflow, WorkflowStep, WorkflowStepStatus, WorkflowTransition


class Command(BaseCommand):
    help = 'Creates the standard claim processing workflow with all necessary steps, statuses, and transitions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of the workflow if it already exists',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Create the workflow if it doesn't exist
                workflow, created = Workflow.objects.get_or_create(
                    name="Claim Processing",
                    defaults={
                        "description": "Standard workflow for processing insurance claims"
                    }
                )

                if not created:
                    if not options.get('force', False):
                        self.stdout.write(self.style.WARNING("Claim Processing workflow already exists. Skipping creation."))
                        return
                    else:
                        # Delete existing workflow if force flag is provided
                        workflow.delete()
                        self.stdout.write(self.style.WARNING("Existing workflow deleted due to --force flag."))
                        workflow = Workflow.objects.create(
                            name="Claim Processing",
                            description="Standard workflow for processing insurance claims"
                        )

                # Create steps for the workflow
                initial_review = WorkflowStep.objects.create(
                    workflow=workflow,
                    name="Initial Review",
                    description="Initial review of the claim by a claims processor",
                    order=1,
                    is_initial_step=True,
                    is_final_step=False
                )

                claim_review = WorkflowStep.objects.create(
                    workflow=workflow,
                    name="Claim Review",
                    description="Detailed review by a claims adjuster",
                    order=2,
                    is_initial_step=False,
                    is_final_step=False
                )

                claim_approval = WorkflowStep.objects.create(
                    workflow=workflow,
                    name="Claim Approval",
                    description="Final approval by a supervisor",
                    order=3,
                    is_initial_step=False,
                    is_final_step=False
                )

                payment_processing = WorkflowStep.objects.create(
                    workflow=workflow,
                    name="Payment Processing",
                    description="Processing payment for approved claims",
                    order=4,
                    is_initial_step=False,
                    is_final_step=False
                )

                claim_completed = WorkflowStep.objects.create(
                    workflow=workflow,
                    name="Claim Completed",
                    description="Claim has been fully processed and completed",
                    order=5,
                    is_initial_step=False,
                    is_final_step=True
                )

                # Create statuses for Initial Review step
                WorkflowStepStatus.objects.create(
                    step=initial_review,
                    name="Submitted",
                    description="Claim has been submitted",
                    is_default_status=True,
                    is_completion_status=False
                )

                WorkflowStepStatus.objects.create(
                    step=initial_review,
                    name="Additional Info Needed",
                    description="More information is needed from the claimant",
                    is_default_status=False,
                    is_completion_status=False
                )

                WorkflowStepStatus.objects.create(
                    step=initial_review,
                    name="Verified",
                    description="Claim has been verified and is ready for detailed review",
                    is_default_status=False,
                    is_completion_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=initial_review,
                    name="On Hold",
                    description="Claim review is temporarily on hold",
                    is_default_status=False,
                    is_completion_status=False,
                    is_on_hold_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=initial_review,
                    name="Cancelled",
                    description="Claim has been cancelled during initial review",
                    is_default_status=False,
                    is_completion_status=False,
                    is_cancellation_status=True
                )

                # Create statuses for Claim Review step
                WorkflowStepStatus.objects.create(
                    step=claim_review,
                    name="In Review",
                    description="Claim is being reviewed by an adjuster",
                    is_default_status=True,
                    is_completion_status=False
                )

                WorkflowStepStatus.objects.create(
                    step=claim_review,
                    name="Reviewed",
                    description="Claim has been reviewed and is ready for approval",
                    is_default_status=False,
                    is_completion_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=claim_review,
                    name="On Hold",
                    description="Claim review is temporarily on hold",
                    is_default_status=False,
                    is_completion_status=False,
                    is_on_hold_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=claim_review,
                    name="Cancelled",
                    description="Claim has been cancelled during review",
                    is_default_status=False,
                    is_completion_status=False,
                    is_cancellation_status=True
                )

                # Create statuses for Claim Approval step
                WorkflowStepStatus.objects.create(
                    step=claim_approval,
                    name="Pending Approval",
                    description="Claim is waiting for supervisor approval",
                    is_default_status=True,
                    is_completion_status=False
                )

                WorkflowStepStatus.objects.create(
                    step=claim_approval,
                    name="Approved",
                    description="Claim has been approved for payment",
                    is_default_status=False,
                    is_completion_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=claim_approval,
                    name="Rejected",
                    description="Claim has been rejected",
                    is_default_status=False,
                    is_completion_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=claim_approval,
                    name="On Hold",
                    description="Claim approval is temporarily on hold",
                    is_default_status=False,
                    is_completion_status=False,
                    is_on_hold_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=claim_approval,
                    name="Cancelled",
                    description="Claim has been cancelled during approval",
                    is_default_status=False,
                    is_completion_status=False,
                    is_cancellation_status=True
                )

                # Create statuses for Payment Processing step
                WorkflowStepStatus.objects.create(
                    step=payment_processing,
                    name="Ready for Payment",
                    description="Claim is ready for payment to be issued",
                    is_default_status=True,
                    is_completion_status=False
                )

                WorkflowStepStatus.objects.create(
                    step=payment_processing,
                    name="Payment Issued",
                    description="Payment has been issued for the claim",
                    is_default_status=False,
                    is_completion_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=payment_processing,
                    name="On Hold",
                    description="Payment is temporarily on hold",
                    is_default_status=False,
                    is_completion_status=False,
                    is_on_hold_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=payment_processing,
                    name="Cancelled",
                    description="Payment has been cancelled",
                    is_default_status=False,
                    is_completion_status=False,
                    is_cancellation_status=True
                )

                # Create statuses for Claim Completed step
                WorkflowStepStatus.objects.create(
                    step=claim_completed,
                    name="Completed",
                    description="Claim has been completed successfully",
                    is_default_status=True,
                    is_completion_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=claim_completed,
                    name="Rejected",
                    description="Claim was rejected",
                    is_default_status=False,
                    is_completion_status=True
                )

                WorkflowStepStatus.objects.create(
                    step=claim_completed,
                    name="Cancelled",
                    description="Claim was cancelled",
                    is_default_status=False,
                    is_completion_status=True,
                    is_cancellation_status=True
                )

                # Create transitions between steps
                # From Initial Review to Claim Review
                WorkflowTransition.objects.create(
                    workflow=workflow,
                    from_step=initial_review,
                    to_step=claim_review,
                    condition="",  # Unconditional transition
                    priority=0,
                    description="Move to detailed review after initial verification"
                )

                # From Claim Review to Claim Approval
                WorkflowTransition.objects.create(
                    workflow=workflow,
                    from_step=claim_review,
                    to_step=claim_approval,
                    condition="",  # Unconditional transition
                    priority=0,
                    description="Move to approval after adjuster review"
                )

                # # From Claim Review to Claim Approval (if amount claims < 1000)
                # WorkflowTransition.objects.create(
                #     workflow=workflow,
                #     from_step=claim_review,
                #     to_step=payment_processing,
                #     condition="float(claim.amount_approved) > 0.0",
                #     priority=1,
                #     description="Move to payment processing for approved claims"
                # )

                # From Claim Approval to Payment Processing (if approved)
                WorkflowTransition.objects.create(
                    workflow=workflow,
                    from_step=claim_approval,
                    to_step=payment_processing,
                    condition="float(claim.amount_approved) > 0.0",  # Only if amount is approved
                    priority=1,
                    description="Move to payment processing for approved claims"
                )

                # From Claim Approval to Claim Completed (if rejected)
                WorkflowTransition.objects.create(
                    workflow=workflow,
                    from_step=claim_approval,
                    to_step=claim_completed,
                    condition="claim.amount_approved is None or float(claim.amount_approved) == 0.0",
                    priority=0,
                    description="Mark as completed (rejected) if no amount is approved"
                )

                # From Payment Processing to Claim Completed
                WorkflowTransition.objects.create(
                    workflow=workflow,
                    from_step=payment_processing,
                    to_step=claim_completed,
                    condition="",  # Unconditional transition
                    priority=0,
                    description="Mark as completed after payment is issued"
                )

                self.stdout.write(self.style.SUCCESS("Claim Processing workflow created successfully."))
                # Don't return the workflow object as it causes Django's stdout.write to fail
        except Exception as e:
            raise CommandError(f"Error creating claim workflow: {str(e)}")
