from .models import ActivityEntry


def log_activity(actor, action, summary, related_resource=None, related_ticket=None):
    """Record one historical fact. Unlike notifications.services.notify(),
    there is no dedupe_key/get_or_create here -- every call is a distinct
    event worth its own row, even if the same field flips back and forth,
    so idempotency would actively lose information rather than help.
    """
    return ActivityEntry.objects.create(
        actor=actor, action=action, summary=summary,
        related_resource=related_resource, related_ticket=related_ticket,
    )
