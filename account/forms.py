from django import forms


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
