from django import template

register = template.Library()


@register.filter
def initials(full_name):
    """First letter of the first and last word of a name, e.g. 'Sam Admin' -> 'SA'."""
    parts = [p for p in (full_name or '').split() if p]
    if not parts:
        return '?'
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@register.filter
def avatar_variant(full_name):
    """Deterministic 1-5 bucket from a name, so the same person always gets the same avatar color."""
    total = sum(ord(c) for c in (full_name or ''))
    return (total % 5) + 1
