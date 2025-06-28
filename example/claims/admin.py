from django.contrib import admin
from .models import Customer, Policy, Claim, ClaimNote, ClaimPayment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'date_joined')
    search_fields = ('name', 'email', 'phone')
    date_hierarchy = 'date_joined'


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('policy_number', 'customer', 'policy_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('policy_type', 'is_active')
    search_fields = ('policy_number', 'customer__name')
    date_hierarchy = 'start_date'


class ClaimNoteInline(admin.TabularInline):
    model = ClaimNote
    extra = 1
    fields = ('user', 'content', 'is_internal', 'created_at')
    readonly_fields = ('created_at',)


class ClaimPaymentInline(admin.TabularInline):
    model = ClaimPayment
    extra = 0
    fields = ('amount', 'payment_date', 'payment_method', 'reference_number', 'processed_by')


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_number', 'policy', 'incident_date', 'filing_date', 'amount_claimed', 'priority')
    list_filter = ('priority', 'incident_date', 'filing_date')
    search_fields = ('claim_number', 'policy__policy_number', 'policy__customer__name')
    date_hierarchy = 'filing_date'
    fieldsets = (
        ('Claim Information', {
            'fields': ('claim_number', 'policy', 'incident_date', 'description', 'amount_claimed', 'priority')
        }),
        ('Location & Documents', {
            'fields': ('incident_location', 'supporting_documents')
        }),
        ('Processing Details', {
            'fields': ('amount_approved', 'adjuster_notes', 'supervisor_notes')
        }),
    )
    readonly_fields = ('claim_number', 'filing_date')
    inlines = [ClaimNoteInline, ClaimPaymentInline]


@admin.register(ClaimNote)
class ClaimNoteAdmin(admin.ModelAdmin):
    list_display = ('claim', 'user', 'created_at', 'is_internal')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('claim__claim_number', 'content', 'user__username')
    date_hierarchy = 'created_at'


@admin.register(ClaimPayment)
class ClaimPaymentAdmin(admin.ModelAdmin):
    list_display = ('claim', 'amount', 'payment_date', 'payment_method', 'processed_by')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('claim__claim_number', 'reference_number')
    date_hierarchy = 'payment_date'
