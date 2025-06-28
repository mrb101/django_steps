from django.apps import AppConfig
from django.apps import AppConfig


class ClaimsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'claims'

    def ready(self):
        # Import here to avoid circular imports
        try:
            from .workflows import get_or_create_claim_workflow
            get_or_create_claim_workflow()
        except Exception as e:
            # Don't crash the app startup, but log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error setting up claim workflow: {e}")

class ClaimsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "claims"
    verbose_name = "Claims"
