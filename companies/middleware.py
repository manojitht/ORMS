from .context import set_current_company


class CurrentCompanyMiddleware:
    """Sets the current-request company context from the logged-in user,
    once per request, so `TenantManager`/`TenantModel` can scope queries
    without every view having to pass it through explicitly.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        company = getattr(user, 'company', None) if user and user.is_authenticated else None
        set_current_company(company)
        try:
            return self.get_response(request)
        finally:
            set_current_company(None)
