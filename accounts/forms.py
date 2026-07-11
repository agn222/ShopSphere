from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Profile


User = get_user_model()


INPUT_CLASSES = (
    "w-full rounded-lg border border-gray-300 px-4 py-3 "
    "focus:border-blue-500 focus:outline-none focus:ring-2 "
    "focus:ring-blue-200"
)


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "you@example.com",
            }
        ),
    )

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "First name",
            }
        ),
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Last name",
            }
        ),
    )

    class Meta:
        model = User

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update(
            {
                "class": INPUT_CLASSES,
                "placeholder": "Password",
            }
        )

        self.fields["password2"].widget.attrs.update(
            {
                "class": INPUT_CLASSES,
                "placeholder": "Confirm password",
            }
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User

        fields = (
            "first_name",
            "last_name",
            "email",
        )

        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
            "last_name": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
            "email": forms.EmailInput(
                attrs={"class": INPUT_CLASSES}
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        existing_user = User.objects.filter(
            email__iexact=email,
        ).exclude(
            pk=self.instance.pk,
        )

        if existing_user.exists():
            raise forms.ValidationError(
                "This email is already being used."
            )

        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile

        fields = (
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
        )

        widgets = {
            field: forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            )
            for field in fields
        }