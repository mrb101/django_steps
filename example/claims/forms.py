from django import forms
from .models import Claim, ClaimNote, Policy, Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3})
        }


class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = ['policy_number', 'customer', 'policy_type', 'start_date', 'end_date', 
                  'premium_amount', 'coverage_amount', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['policy', 'incident_date', 'description', 'amount_claimed', 
                  'priority', 'supporting_documents', 'incident_location']
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ClaimReviewForm(forms.ModelForm):
    """Form for adjusters to review claims"""
    class Meta:
        model = Claim
        fields = ['amount_approved', 'adjuster_notes']
        widgets = {
            'adjuster_notes': forms.Textarea(attrs={'rows': 3}),
        }


class ClaimApprovalForm(forms.ModelForm):
    """Form for supervisors to approve or deny claims"""
    class Meta:
        model = Claim
        fields = ['supervisor_notes']
        widgets = {
            'supervisor_notes': forms.Textarea(attrs={'rows': 3}),
        }


class ClaimNoteForm(forms.ModelForm):
    class Meta:
        model = ClaimNote
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }
