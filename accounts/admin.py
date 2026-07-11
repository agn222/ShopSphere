from django.contrib import admin

from .models import Profile, Wishlist


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone_number",
        "city",
        "state",
        "postal_code",
        "country",
    )

    search_fields = (
        "user__username",
        "user__email",
        "phone_number",
        "city",
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "product_count",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
    )

    filter_horizontal = (
        "products",
    )

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = "Products"