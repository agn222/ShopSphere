from django.conf import settings
from django.db import models
from django.urls import reverse
from decimal import Decimal

from store.models import Product
class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED = "fixed", "Fixed amount"

    code = models.CharField(
        max_length=50,
        unique=True,
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    active = models.BooleanField(default=True)

    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    usage_limit = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    used_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    def is_usage_available(self):
        if self.usage_limit is None:
            return True

        return self.used_count < self.usage_limit

    def calculate_discount(self, subtotal):
        subtotal = Decimal(subtotal)

        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = (
                subtotal * self.discount_value
            ) / Decimal("100")
        else:
            discount = self.discount_value

        return min(discount, subtotal)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.CASCADE,
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)

    address_line_1 = models.CharField(max_length=255)

    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
    )

    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)

    country = models.CharField(
        max_length=100,
        default="India",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    paid = models.BooleanField(default=False)

    # Razorpay payment details
    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
    )
    coupon = models.ForeignKey(
    Coupon,
    related_name="orders",
    on_delete=models.SET_NULL,
    blank=True,
    null=True,
)

    coupon_code = models.CharField(
    max_length=50,
    blank=True,
)

    discount = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0,
)

    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
    )

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id}"

    def get_subtotal(self):
     return sum(
        item.get_cost()
        for item in self.items.all()
    )


    def get_total_price(self):
     total = self.get_subtotal() - self.discount

     return max(total, Decimal("0.00"))

    def get_absolute_url(self):
        return reverse(
            "orders:order_detail",
            args=[self.id],
        )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
    )

    product = models.ForeignKey(
        Product,
        related_name="order_items",
        on_delete=models.PROTECT,
    )

    product_name = models.CharField(max_length=200)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

    def get_cost(self):
        return self.price * self.quantity