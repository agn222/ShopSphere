from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review

        fields = (
            "rating",
            "comment",
        )

        widgets = {
            "rating": forms.Select(
                choices=[
                    (5, "5 - Excellent"),
                    (4, "4 - Very Good"),
                    (3, "3 - Good"),
                    (2, "2 - Fair"),
                    (1, "1 - Poor"),
                ],
                attrs={
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-3"
                    ),
                },
            ),

            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Share your experience with this product..."
                    ),
                    "class": (
                        "w-full rounded-lg border "
                        "border-gray-300 px-4 py-3 "
                        "focus:border-blue-500 "
                        "focus:outline-none "
                        "focus:ring-2 "
                        "focus:ring-blue-200"
                    ),
                }
            ),
        }

    def clean_comment(self):
        comment = self.cleaned_data["comment"].strip()

        if len(comment) < 10:
            raise forms.ValidationError(
                "Your review must contain at least 10 characters."
            )

        return comment