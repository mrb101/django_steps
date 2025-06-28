import logging
from django.contrib.contenttypes.models import ContentType
import uuid

logger = logging.getLogger(__name__)

def extract_context_data_from_content_object(content_object):
    """
    Extracts data from a content object for use in CEL expressions.

    Args:
        content_object: A Django model instance

    Returns:
        dict: A dictionary of field values
    """
    context_data = {}

    if not content_object:
        return context_data

    try:
        # Attempt to convert content_object fields to a dictionary for CEL evaluation
        if hasattr(content_object, '_meta') and hasattr(content_object._meta, 'fields'):
            for field in content_object._meta.fields:
                if field.name != "id":  # 'id' is already in object_id, avoid conflicts
                    value = getattr(content_object, field.name)
                    # Convert UUIDs to string for CEL compatibility
                    if isinstance(value, uuid.UUID):
                        value = str(value)
                    context_data[field.name] = value

        # If content_object has a direct to_dict or serialize method, use it
        if hasattr(content_object, "to_dict"):
            context_data.update(content_object.to_dict())

        # Add the entire object for direct attribute access
        if hasattr(content_object, '_meta'):
            content_type = ContentType.objects.get_for_model(content_object)
            context_data[content_type.model] = context_data  # Alias for clarity in CEL
    except (AttributeError, TypeError) as e:
        logger.warning(f"Could not extract context data from content_object: {e}")

    return context_data
