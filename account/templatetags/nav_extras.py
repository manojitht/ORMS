from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context, *url_names):
    """Return 'active' when the current view's url_name is in url_names.

    Sidebar sections often fan out across several views that share a
    Django app (e.g. resources:view_resource_categories vs.
    resources:resources_listings_page both live under the 'resources' app),
    so app_name alone can't tell two sidebar sections apart — matching on
    the specific url_name is the only reliable signal.
    """
    request = context.get('request')
    if not request or not request.resolver_match:
        return ''
    return 'active' if request.resolver_match.url_name in url_names else ''
