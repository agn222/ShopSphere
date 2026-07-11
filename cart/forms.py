from django import forms


PRODUCT_QUANTITY_CHOICES = [
    (number, str(number))
    for number in range(1, 11)
]


class CartAddProductForm(forms.Form):
    quantity = forms.TypedChoiceField(
        choices=PRODUCT_QUANTITY_CHOICES,
        coerce=int,
        initial=1,
    )

    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput,
    )