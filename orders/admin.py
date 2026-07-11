from django.contrib import admin
from .models import Coupon, Order, OrderItem

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product",
        "product_name",
        "price",
        "quantity",
    )

    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "first_name",
        "last_name",
        "status",
        "paid",
        "created_at",
        "coupon_code",
        "discount",
    )

    list_filter = (
        "status",
        "paid",
        "created_at",
    )

    search_fields = (
        "id",
        "user__username",
        "email",
        "phone_number",
        "first_name",
        "last_name",
    )

    list_editable = (
        "status",
        "paid",
    )

    readonly_fields = (
    "user",
    "razorpay_order_id",
    "razorpay_payment_id",
    "razorpay_signature",
    "created_at",
    "updated_at",
)

    inlines = [
        OrderItemInline,
    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product_name",
        "price",
        "quantity",
    )

    search_fields = (
        "product_name",
        "order__id",
    )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "minimum_order_amount",
        "active",
        "valid_from",
        "valid_until",
        "used_count",
        "usage_limit",
        
    )

    list_filter = (
        "active",
        "discount_type",
        "valid_from",
        "valid_until",
    )

    search_fields = (
        "code",
    )

    readonly_fields = (
        "used_count",
        "created_at",
    )