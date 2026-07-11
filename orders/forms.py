from django import forms
from django.utils import timezone

from .models import Coupon, Order


INPUT_CLASSES = (
    "w-full rounded-lg border border-gray-300 px-4 py-3 "
    "focus:border-blue-500 focus:outline-none "
    "focus:ring-2 focus:ring-blue-200"
)


class OrderCreateForm(forms.ModelForm):

    coupon_code = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Enter coupon code",
            }
        ),
    )

    class Meta:
        model = Order

        fields = (
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
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
            "phone_number": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
            "address_line_1": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
            "address_line_2": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
            "city": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
            "state": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
            "postal_code": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
            "country": forms.TextInput(
                attrs={"class": INPUT_CLASSES}
            ),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"].strip()

        if not phone_number.isdigit():
            raise forms.ValidationError(
                "Enter a valid phone number using digits only."
            )

        if len(phone_number) < 10 or len(phone_number) > 15:
            raise forms.ValidationError(
                "Phone number must contain 10 to 15 digits."
            )

        return phone_number

    def clean_coupon_code(self):
        coupon_code = self.cleaned_data.get(
            "coupon_code",
            "",
        ).strip().upper()

        if not coupon_code:
            return ""

        try:
            coupon = Coupon.objects.get(
                code__iexact=coupon_code,
                active=True,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now(),
            )

        except Coupon.DoesNotExist:
            raise forms.ValidationError(
                "This coupon is invalid or expired."
            )

        if not coupon.is_usage_available():
            raise forms.ValidationError(
                "This coupon has reached its usage limit."
            )

        return coupon.code

    def clean_postal_code(self):
        postal_code = self.cleaned_data["postal_code"].strip()

        if not postal_code.isdigit():
            raise forms.ValidationError(
                "Postal code must contain digits only."
            )

        if len(postal_code) != 6:
            raise forms.ValidationError(
                "Enter a valid 6-digit postal code."
            )

        return postal_code