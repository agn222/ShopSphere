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
                        "w-full rounded-xl border border-slate-200 "
            "bg-white px-4 py-3.5 font-medium text-slate-800 "
            "outline-none transition focus:border-blue-500 "
            "focus:ring-4 focus:ring-blue-100"
                    ),
                },
            ),

            "comment": forms.Textarea(
                attrs={
                    "rows": 5,
        "placeholder": "What did you like or dislike about this product?",
        "class": (
            "w-full resize-none rounded-xl border border-slate-200 "
            "bg-white px-4 py-3.5 text-slate-800 outline-none "
            "transition placeholder:text-slate-400 "
            "focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
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