from django import forms
from .models import Account
from django.contrib.auth.forms import UserCreationForm


class LoginUsers(forms.Form):
    peoplesoft_id = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-login"
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-login"
            }
        )
    )


# class CreateSystemUsers(UserCreationForm):
#     peoplesoft_id = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "r-p-textbox"
#             }
#         )
#     )

#     first_name = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "r-p-textbox"
#             }
#         )
#     )

#     last_name = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "r-p-textbox"
#             }
#         )
#     )

#     email = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "r-p-textbox"
#             }
#         )
#     )

#     department = forms.CharField(
#         widget=forms.Select(
#             attrs={
#                 "class": "r-p-textbox"
#             }
#         )
#     )

#     team_name = forms.CharField(
#         widget=forms.Select(
#             attrs={
#                 "class": "r-p-textbox"
#             }
#         )
#     )

#     user_role = forms.CharField(
#         widget=forms.Select(
#             attrs={
#                 "class": "r-p-textbox"
#             }
#         )
#     )

#     password = forms.CharField(
#         widget=forms.HiddenInput(
#             attrs={
#                 "class": "r-p-textbox"
#             }
#         )
#     )

    class Meta:
        model = Account
        fields = ('peoplesoft_id', 'first_name', 'last_name', 'email', 'department', 'team', 'role', 'password')
