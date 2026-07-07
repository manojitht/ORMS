import secrets
import string

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

# Shared by any app that provisions an Account (account/views.py's
# superadmin-driven add_user_page, employees/views.py's self-service
# "grant portal access" flow) so both use the exact same temp-password
# scheme and activation-email pattern rather than duplicating it.


def generate_temporary_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_account_creation_email(request, user):
    """Email the new user their account-activation link. Deletes the account
    and returns False if the email fails to send, so we don't leave behind
    an account the owner has no way to activate."""
    try:
        current_site = get_current_site(request)
        context = {
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        }
        text_body = render_to_string('account/account_confirmation_email.html', context)
        html_body = render_to_string('account/emails/account_confirmation_email.html', context)
        email = EmailMultiAlternatives('Sukhra account creation', text_body, to=[user.email])
        email.attach_alternative(html_body, 'text/html')
        email.send()
        return True
    except Exception:
        user.delete()
        return False
