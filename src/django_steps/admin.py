from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (Workflow, WorkflowInstance, WorkflowStep,
                     WorkflowStepStatus, WorkflowTransition)
from .services import (cancel_workflow_instance, resume_workflow_instance,
                       set_workflow_on_hold)


class WorkflowStepStatusInline(admin.TabularInline):
    model = WorkflowStepStatus
    extra = 1
    fields = (
        "name",
        "description",
        "is_default_status",
        "is_completion_status",
        "is_cancellation_status",
        "is_on_hold_status",
    )


class WorkflowTransitionInline(admin.TabularInline):
    model = WorkflowTransition
    fk_name = "from_step"  # Specify which ForeignKey points to the parent model
    extra = 1
    fields = ("to_step", "condition", "priority", "description")
    raw_id_fields = ("to_step",)  # Use raw_id_fields for related steps


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ("workflow", "name", "order", "is_initial_step", "is_final_step")
    list_filter = ("workflow", "is_initial_step", "is_final_step")
    search_fields = ("name", "description", "workflow__name")
    inlines = [
        WorkflowStepStatusInline,
        WorkflowTransitionInline,
    ]  # Add transitions here
    raw_id_fields = ("workflow",)
    ordering = (
        "workflow__name",
        "order",
    )

    fieldsets = (
        (
            None,
            {
                "fields": ("workflow", "name", "description", "order"),
            },
        ),
        (
            "Step Flags",
            {
                "fields": ("is_initial_step", "is_final_step"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")



class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 1
    fields = ("name", "description", "order", "is_initial_step", "is_final_step")


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")
    inlines = [WorkflowStepInline]
    ordering = ("name",)

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "description"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "workflow",
        "content_object",
        "current_step",
        "current_step_status",
        "started_at",
        "completed_at",
    )
    list_filter = ("workflow", "current_step", "current_step_status", "content_type")
    search_fields = (
        "id",
        "object_id",
        "workflow__name",
        "current_step__name",
        "current_step_status__name",
    )
    readonly_fields = ("id", "started_at", "completed_at", "content_object")
    raw_id_fields = ("workflow", "current_step", "current_step_status", "content_type")
    date_hierarchy = "started_at"
    ordering = ("-started_at",)

    fieldsets = (
        (
            "Workflow Instance Details",
            {
                "fields": ("workflow", "content_type", "object_id", "content_object"),
            },
        ),
        (
            "Current State",
            {
                "fields": ("current_step", "current_step_status"),
            },
        ),
        (
            "Timestamps & Completion",
            {
                "fields": ("started_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_on_hold", "mark_as_resumed", "mark_as_cancelled"]

    @admin.action(description="Mark selected workflows as On Hold")
    def mark_as_on_hold(self, request, queryset):
        successful_updates = 0
        for instance in queryset:
            if set_workflow_on_hold(instance):
                successful_updates += 1
            else:
                self.message_user(
                    request,
                    f"Failed to put workflow instance {instance.id} on hold.",
                    level=messages.ERROR,
                )
        if successful_updates > 0:
            self.message_user(
                request,
                f"Successfully put {successful_updates} workflow instances on hold.",
            )

    @admin.action(description="Mark selected workflows as Resumed")
    def mark_as_resumed(self, request, queryset):
        successful_updates = 0
        for instance in queryset:
            if resume_workflow_instance(instance):
                successful_updates += 1
            else:
                self.message_user(
                    request,
                    f"Failed to resume workflow instance {instance.id}.",
                    level=messages.ERROR,
                )
        if successful_updates > 0:
            self.message_user(
                request,
                f"Successfully resumed {successful_updates} workflow instances.",
            )

    @admin.action(description="Mark selected workflows as Cancelled")
    def mark_as_cancelled(self, request, queryset):
        successful_updates = 0
        for instance in queryset:
            if cancel_workflow_instance(instance):
                successful_updates += 1
            else:
                self.message_user(
                    request,
                    f"Failed to cancel workflow instance {instance.id}.",
                    level=messages.ERROR,
                )
        if successful_updates > 0:
            self.message_user(
                request,
                f"Successfully cancelled {successful_updates} workflow instances.",
            )


@admin.register(WorkflowStepStatus)
class WorkflowStepStatusAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "step",
        "is_default_status",
        "is_completion_status",
        "is_cancellation_status",
        "is_on_hold_status",
        "created_at",
    )
    list_filter = (
        "step__workflow",
        "step",
        "is_default_status",
        "is_completion_status",
        "is_cancellation_status",
        "is_on_hold_status",
    )
    search_fields = ("name", "description", "step__name", "step__workflow__name")
    raw_id_fields = ("step",)
    ordering = ("step__workflow__name", "step__order", "name")

    fieldsets = (
        (
            None,
            {
                "fields": ("step", "name", "description"),
            },
        ),
        (
            "Status Flags",
            {
                "fields": (
                    "is_default_status",
                    "is_completion_status",
                    "is_cancellation_status",
                    "is_on_hold_status",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(WorkflowTransition)
class WorkflowTransitionAdmin(admin.ModelAdmin):
    list_display = (
        "workflow",
        "from_step",
        "to_step",
        "condition",
        "priority",
        "description",
    )
    list_filter = ("workflow", "from_step__workflow", "from_step", "to_step")
    search_fields = (
        "condition",
        "description",
        "from_step__name",
        "to_step__name",
        "workflow__name",
    )
    raw_id_fields = ("workflow", "from_step", "to_step")
    ordering = ("workflow__name", "from_step__order", "-priority")

    fieldsets = (
        (
            None,
            {
                "fields": ("workflow", "from_step", "to_step", "condition", "priority"),
            },
        ),
        (
            "Description",
            {
                "fields": ("description",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")
