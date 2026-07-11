from django.contrib import admin
from .models import Category, Product, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    search_fields = (
        "name",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock",
        "is_available",
        "is_featured",
        "created_at",
    )

    list_filter = (
        "category",
        "is_available",
        "is_featured",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    list_editable = (
        "price",
        "stock",
        "is_available",
        "is_featured",
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "user",
        "rating",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    search_fields = (
        "product__name",
        "user__username",
        "user__email",
        "comment",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )