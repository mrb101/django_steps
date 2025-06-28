from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.conf import settings


class Customer(models.Model):
    """Represents a customer who can submit insurance claims"""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Policy(models.Model):
    """Represents an insurance policy held by a customer"""
    POLICY_TYPES = [
        ('AUTO', 'Auto Insurance'),
        ('HOME', 'Home Insurance'),
        ('HEALTH', 'Health Insurance'),
        ('LIFE', 'Life Insurance'),
    ]

    policy_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='policies')
    policy_type = models.CharField(max_length=10, choices=POLICY_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.policy_number} - {self.get_policy_type_display()} for {self.customer.name}"

    def is_expired(self):
        return timezone.now().date() > self.end_date


class Claim(models.Model):
    """Represents an insurance claim submitted by a customer"""
    CLAIM_PRIORITIES = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
        ('URGENT', 'Urgent Priority'),
    ]

    claim_number = models.CharField(max_length=20, unique=True)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='claims')
    incident_date = models.DateField()
    filing_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    amount_claimed = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    priority = models.CharField(max_length=10, choices=CLAIM_PRIORITIES, default='MEDIUM')
    supporting_documents = models.FileField(upload_to='claim_documents/', blank=True, null=True)
    incident_location = models.CharField(max_length=255, blank=True)

    # Fields that will be updated during workflow
    amount_approved = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    adjuster_notes = models.TextField(blank=True)
    supervisor_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Claim {self.claim_number} - {self.policy.customer.name}"

    def save(self, *args, **kwargs):
        # Generate a claim number if not provided
        if not self.claim_number:
            # Use the current timestamp and policy number to create a unique claim number
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.claim_number = f"CLM-{self.policy.policy_type}-{timestamp}"

        super().save(*args, **kwargs)

    @property
    def workflow_instance(self):
        """Returns the associated workflow instance using ContentType framework"""
        from django.contrib.contenttypes.models import ContentType
        from django_steps.models import WorkflowInstance

        content_type = ContentType.objects.get_for_model(self.__class__)
        try:
            return WorkflowInstance.objects.filter(
                content_type=content_type,
                object_id=str(self.pk)
            ).order_by('-started_at').first()
        except Exception:
            return None


class ClaimNote(models.Model):
    """Represents notes added to a claim during processing"""
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="If checked, this note is only visible to staff")

    def __str__(self):
        return f"Note on {self.claim.claim_number} by {self.user.username} at {self.created_at}"


class ClaimPayment(models.Model):
    """Represents payments made for approved claims"""
    PAYMENT_METHODS = [
        ('CHECK', 'Check'),
        ('DIRECT_DEPOSIT', 'Direct Deposit'),
        ('WIRE', 'Wire Transfer'),
    ]

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=50, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Payment of ${self.amount} for {self.claim.claim_number}"
