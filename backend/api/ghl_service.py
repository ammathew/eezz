import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GHLService:
    """Service for managing GoHighLevel contacts"""

    BASE_URL = "https://services.leadconnectorhq.com"

    @staticmethod
    def create_contact(email, first_name=None, last_name=None, tags=None, custom_fields=None):
        """
        Create a contact in GoHighLevel

        Args:
            email: Contact email address (required)
            first_name: Contact first name (optional)
            last_name: Contact last name (optional)
            tags: List of tags to assign to the contact (optional)
            custom_fields: Dictionary of custom field key-value pairs (optional)

        Returns:
            dict: Response from GHL API with contact data, or None if failed
        """
        if not hasattr(settings, 'GHL_API_TOKEN') or not settings.GHL_API_TOKEN:
            logger.error("GHL_API_TOKEN not configured in settings")
            return None

        if not hasattr(settings, 'GHL_LOCATION_ID') or not settings.GHL_LOCATION_ID:
            logger.error("GHL_LOCATION_ID not configured in settings")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {settings.GHL_API_TOKEN}",
                "Content-Type": "application/json",
                "Version": "2021-07-28"
            }

            payload = {
                "email": email,
                "locationId": settings.GHL_LOCATION_ID,
            }

            if first_name:
                payload["firstName"] = first_name
            if last_name:
                payload["lastName"] = last_name
            if tags:
                payload["tags"] = tags if isinstance(tags, list) else [tags]
            if custom_fields:
                # Convert custom_fields dict to array format expected by GHL
                payload["customFields"] = [
                    {"key": key, "field_value": value}
                    for key, value in custom_fields.items()
                ]

            logger.info(f"Creating GHL contact for {email}")

            response = requests.post(
                f"{GHLService.BASE_URL}/contacts/",
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info(f"Successfully created GHL contact for {email}")
                return response.json()
            else:
                logger.error(
                    f"Failed to create GHL contact for {email}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Timeout while creating GHL contact for {email}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while creating GHL contact for {email}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating GHL contact for {email}: {type(e).__name__}: {str(e)}")
            return None

    @staticmethod
    def create_contact_from_dream_submission(submission):
        """
        Create a GHL contact from a PublicDreamSubmission

        Args:
            submission: PublicDreamSubmission instance

        Returns:
            dict: Response from GHL API with contact data, or None if failed
        """
        if not submission.email:
            logger.error(f"No email provided for submission {submission.submission_id}")
            return None

        # Extract first name if email contains it (e.g., john.doe@example.com -> John)
        email_name = submission.email.split('@')[0]
        first_name = email_name.split('.')[0].capitalize() if '.' in email_name else email_name.capitalize()

        # Add tag for tracking
        tags = ["unravel-public"]

        # Add custom fields with dream submission details
        custom_fields = {
            "submission_id": str(submission.submission_id),
            "dream_submitted_at": submission.created_at.isoformat(),
        }

        return GHLService.create_contact(
            email=submission.email,
            first_name=first_name,
            tags=tags,
            custom_fields=custom_fields
        )
