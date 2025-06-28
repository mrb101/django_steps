from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.utils import timezone

from .models import Claim, Customer, Policy, ClaimNote, ClaimPayment
from .forms import ClaimForm, ClaimNoteForm, ClaimReviewForm, ClaimApprovalForm, CustomerForm, PolicyForm

from django_steps.models import WorkflowStep
from django_steps.services import (
    start_workflow_instance, update_workflow_step_status, 
    cancel_workflow_instance, get_workflow_instance_for_object
)


# Dashboard View
@login_required
def dashboard(request):
    # Get counts for different entities
    total_customers = Customer.objects.count()
    total_policies = Policy.objects.count()
    total_claims = Claim.objects.count()
    recent_claims = Claim.objects.order_by('-filing_date')[:5]

    # Claims statistics
    claims_by_priority = {
        priority[0]: Claim.objects.filter(priority=priority[0]).count()
        for priority in Claim.CLAIM_PRIORITIES
    }

    # Policy statistics
    policies_by_type = {
        policy_type[0]: Policy.objects.filter(policy_type=policy_type[0]).count()
        for policy_type in Policy.POLICY_TYPES
    }

    context = {
        'total_customers': total_customers,
        'total_policies': total_policies,
        'total_claims': total_claims,
        'recent_claims': recent_claims,
        'claims_by_priority': claims_by_priority,
        'policies_by_type': policies_by_type,
    }

    return render(request, 'claims/dashboard.html', context)


# Customer Views
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'claims/customer_list.html'
    context_object_name = 'customers'
    ordering = ['name']
    paginate_by = 10


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'claims/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['policies'] = self.object.policies.all()
        # Get all claims across all policies for this customer
        claims = Claim.objects.filter(policy__customer=self.object).order_by('-filing_date')
        context['claims'] = claims
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'claims/customer_form.html'
    success_url = reverse_lazy('claims:customer-list')

    def form_valid(self, form):
        messages.success(self.request, 'Customer created successfully!')
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'claims/customer_form.html'

    def get_success_url(self):
        return reverse('claims:customer-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Customer updated successfully!')
        return super().form_valid(form)


# Policy Views
class PolicyListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = 'claims/policy_list.html'
    context_object_name = 'policies'
    ordering = ['-start_date']
    paginate_by = 10


class PolicyDetailView(LoginRequiredMixin, DetailView):
    model = Policy
    template_name = 'claims/policy_detail.html'
    context_object_name = 'policy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['claims'] = self.object.claims.all().order_by('-filing_date')
        return context


class PolicyCreateView(LoginRequiredMixin, CreateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'claims/policy_form.html'

    def get_initial(self):
        initial = super().get_initial()
        if 'customer_id' in self.kwargs:
            initial['customer'] = self.kwargs['customer_id']
        return initial

    def get_success_url(self):
        if 'customer_id' in self.kwargs:
            return reverse('claims:customer-detail', kwargs={'pk': self.kwargs['customer_id']})
        return reverse('claims:policy-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Policy created successfully!')
        return super().form_valid(form)


class PolicyUpdateView(LoginRequiredMixin, UpdateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'claims/policy_form.html'

    def get_success_url(self):
        return reverse('claims:policy-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Policy updated successfully!')
        return super().form_valid(form)


# Claim Views
class ClaimListView(LoginRequiredMixin, ListView):
    model = Claim
    template_name = 'claims/claim_list.html'
    context_object_name = 'claims'
    ordering = ['-filing_date']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by priority if specified
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filter by policy type if specified
        policy_type = self.request.GET.get('policy_type')
        if policy_type:
            queryset = queryset.filter(policy__policy_type=policy_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['priorities'] = Claim.CLAIM_PRIORITIES
        context['policy_types'] = Policy.POLICY_TYPES
        context['current_priority'] = self.request.GET.get('priority', '')
        context['current_policy_type'] = self.request.GET.get('policy_type', '')
        return context


class ClaimDetailView(LoginRequiredMixin, DetailView):
    model = Claim
    template_name = 'claims/claim_detail.html'
    context_object_name = 'claim'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get claim notes for this claim
        if self.request.user.is_staff:
            # Staff can see all notes
            context['notes'] = self.object.notes.all().order_by('-created_at')
        else:
            # Non-staff can only see non-internal notes
            context['notes'] = self.object.notes.filter(is_internal=False).order_by('-created_at')

        # Get payments for this claim
        context['payments'] = self.object.payments.all().order_by('-payment_date')

        # Add form for adding notes
        context['note_form'] = ClaimNoteForm()

        # Check if there's a workflow instance for this claim
        workflow_instance = get_workflow_instance_for_object(self.object)
        context['workflow_instance'] = workflow_instance

        # Based on the current workflow step, determine which forms to show
        if workflow_instance and workflow_instance.current_step:
            step_name = workflow_instance.current_step.name

            if step_name == 'Claim Review':
                context['review_form'] = ClaimReviewForm(instance=self.object)
            elif step_name == 'Claim Approval':
                context['approval_form'] = ClaimApprovalForm(instance=self.object)

        return context


class ClaimCreateView(LoginRequiredMixin, CreateView):
    model = Claim
    form_class = ClaimForm
    template_name = 'claims/claim_form.html'

    def get_initial(self):
        initial = super().get_initial()
        if 'policy_id' in self.kwargs:
            initial['policy'] = self.kwargs['policy_id']
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)

        # Start a workflow for this claim
        try:
            workflow_instance = start_workflow_instance('Claim Processing', self.object)
            if workflow_instance:
                messages.success(self.request, 'Claim created and workflow started successfully!')
            else:
                messages.warning(self.request, 'Claim created but could not start workflow.')
        except Exception as e:
            messages.error(self.request, f'Error starting workflow: {str(e)}')

        return response

    def get_success_url(self):
        return reverse('claims:claim-detail', kwargs={'pk': self.object.pk})


@login_required
def add_claim_note(request, pk):
    claim = get_object_or_404(Claim, pk=pk)

    if request.method == 'POST':
        form = ClaimNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.claim = claim
            note.user = request.user
            note.save()
            messages.success(request, 'Note added successfully!')
        else:
            messages.error(request, 'Error adding note. Please check the form.')

    return redirect('claims:claim-detail', pk=pk)


@login_required
def start_claim_review(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    workflow_instance = get_workflow_instance_for_object(claim)

    if not workflow_instance or workflow_instance.current_step.name != 'Initial Review':
        messages.error(request, 'This claim is not in the initial review stage.')
        return redirect('claims:claim-detail', pk=pk)

    # Update workflow step to 'Claim Review'
    next_step = WorkflowStep.objects.get(workflow=workflow_instance.workflow, name='Claim Review')
    workflow_instance.current_step = next_step
    workflow_instance.save()

    # Add a note about starting the review process
    ClaimNote.objects.create(
        claim=claim,
        user=request.user,
        content="Claim review process started",
        is_internal=True
    )

    messages.success(request, 'Claim moved to review stage. You can now perform the review.')
    return redirect('claims:claim-detail', pk=pk)

@login_required
def process_claim_review(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    workflow_instance = get_workflow_instance_for_object(claim)

    if not workflow_instance or workflow_instance.current_step.name != 'Claim Review':
        messages.error(request, 'This claim is not currently in the review stage.')
        return redirect('claims:claim-detail', pk=pk)

    if request.method == 'POST':
        form = ClaimReviewForm(request.POST, instance=claim)
        if form.is_valid():
            form.save()

            # Add a note about the review
            ClaimNote.objects.create(
                claim=claim,
                user=request.user,
                content=f"Claim reviewed. Amount approved: ${claim.amount_approved}",
                is_internal=True
            )

            # Update workflow status based on form data
            if claim.amount_approved is not None:
                # Move to the next step
                update_workflow_step_status(workflow_instance, 'Reviewed')
                messages.success(request, 'Claim review completed and moved to approval stage.')
            else:
                messages.warning(request, 'Claim saved but not advanced as no amount was approved.')
        else:
            messages.error(request, 'Error processing review. Please check the form.')

    return redirect('claims:claim-detail', pk=pk)


@login_required
def process_claim_approval(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    workflow_instance = get_workflow_instance_for_object(claim)

    if not workflow_instance or workflow_instance.current_step.name != 'Claim Approval':
        messages.error(request, 'This claim is not currently in the approval stage.')
        return redirect('claims:claim-detail', pk=pk)

    if request.method == 'POST':
        form = ClaimApprovalForm(request.POST, instance=claim)
        if form.is_valid():
            form.save()

            # Extract the decision from the form
            decision = request.POST.get('decision')

            # Add a note about the approval/rejection
            ClaimNote.objects.create(
                claim=claim,
                user=request.user,
                content=f"Supervisor {decision}: {claim.supervisor_notes}",
                is_internal=True
            )

            # Update workflow status based on decision
            if decision == 'approve':
                update_workflow_step_status(workflow_instance, 'Approved')
                messages.success(request, 'Claim approved successfully!')
            elif decision == 'reject':
                update_workflow_step_status(workflow_instance, 'Rejected')
                messages.success(request, 'Claim rejected.')
            else:
                messages.warning(request, 'No decision provided. Claim saved but status not updated.')
        else:
            messages.error(request, 'Error processing approval. Please check the form.')

    return redirect('claims:claim-detail', pk=pk)


@login_required
def cancel_claim(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    workflow_instance = get_workflow_instance_for_object(claim)

    if not workflow_instance:
        messages.error(request, 'No active workflow found for this claim.')
        return redirect('claims:claim-detail', pk=pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided')

        # Cancel the workflow
        if cancel_workflow_instance(workflow_instance):
            # Add a note about the cancellation
            ClaimNote.objects.create(
                claim=claim,
                user=request.user,
                content=f"Claim cancelled. Reason: {reason}",
                is_internal=True
            )
            messages.success(request, 'Claim cancelled successfully!')
        else:
            messages.error(request, 'Failed to cancel the claim workflow.')

    return redirect('claims:claim-detail', pk=pk)


@login_required
def process_claim_payment(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    workflow_instance = get_workflow_instance_for_object(claim)

    # Check if claim is approved and in Payment step
    if not workflow_instance or workflow_instance.current_step.name != 'Payment Processing':
        messages.error(request, 'This claim is not ready for payment processing.')
        return redirect('claims:claim-detail', pk=pk)

    if request.method == 'POST':
        # Create a payment record
        payment_amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        reference_number = request.POST.get('reference_number', '')
        payment_notes = request.POST.get('notes', '')

        try:
            # Validate payment amount
            payment_amount = float(payment_amount)
            if payment_amount <= 0 or payment_amount > claim.amount_approved:
                raise ValueError('Invalid payment amount')

            # Create the payment record
            ClaimPayment.objects.create(
                claim=claim,
                amount=payment_amount,
                payment_date=timezone.now().date(),
                payment_method=payment_method,
                reference_number=reference_number,
                processed_by=request.user,
                notes=payment_notes
            )

            # Update workflow status
            update_workflow_step_status(workflow_instance, 'Payment Issued')

            # Add a note about the payment
            ClaimNote.objects.create(
                claim=claim,
                user=request.user,
                content=f"Payment of ${payment_amount} issued via {payment_method}.",
                is_internal=False  # Make this visible to customer
            )

            messages.success(request, 'Payment processed successfully!')
        except ValueError:
            messages.error(request, 'Invalid payment amount. Must be positive and not exceed approved amount.')
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')

    return redirect('claims:claim-detail', pk=pk)
