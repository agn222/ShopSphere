from decimal import Decimal
from django.http import FileResponse

from .invoice_utils import generate_invoice_pdf

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from razorpay.errors import SignatureVerificationError

from cart.cart import Cart
from store.models import Product

from .email_utils import send_order_confirmation_email
from .forms import OrderCreateForm
from .models import Coupon, Order, OrderItem


def get_razorpay_client():
    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )


@login_required
def order_create(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.error(
            request,
            "Your cart is empty.",
        )
        return redirect("store:product_list")

    profile = getattr(
        request.user,
        "profile",
        None,
    )

    initial_data = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
    }

    if profile:
        initial_data.update(
            {
                "phone_number": profile.phone_number,
                "address_line_1": profile.address_line_1,
                "address_line_2": profile.address_line_2,
                "city": profile.city,
                "state": profile.state,
                "postal_code": profile.postal_code,
                "country": profile.country,
            }
        )

    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():

                    # Validate stock using locked product rows.
                    for item in cart:
                        product = (
                            Product.objects
                            .select_for_update()
                            .get(id=item["product"].id)
                        )

                        if not product.is_available:
                            raise ValueError(
                                f"{product.name} is no longer available."
                            )

                        if item["quantity"] > product.stock:
                            raise ValueError(
                                f"Only {product.stock} unit(s) of "
                                f"{product.name} are available."
                            )

                    coupon = None

                    coupon_code = form.cleaned_data.get(
                        "coupon_code",
                        "",
                    )

                    cart_subtotal = cart.get_total_price()

                    # Validate the coupon again inside the transaction.
                    if coupon_code:
                        coupon = (
                            Coupon.objects
                            .select_for_update()
                            .filter(
                                code__iexact=coupon_code,
                                active=True,
                                valid_from__lte=timezone.now(),
                                valid_until__gte=timezone.now(),
                            )
                            .first()
                        )

                        if coupon is None:
                            raise ValueError(
                                "The selected coupon is no longer valid."
                            )

                        if not coupon.is_usage_available():
                            raise ValueError(
                                "This coupon has reached its usage limit."
                            )

                        if (
                            cart_subtotal
                            < coupon.minimum_order_amount
                        ):
                            raise ValueError(
                                "This coupon requires a minimum "
                                f"order of ₹{coupon.minimum_order_amount}."
                            )

                    order = form.save(commit=False)
                    order.user = request.user

                    if coupon:
                        order.coupon = coupon
                        order.coupon_code = coupon.code
                        order.discount = coupon.calculate_discount(
                            cart_subtotal
                        )

                    order.save()

                    # Store a snapshot of each ordered item.
                    for item in cart:
                        OrderItem.objects.create(
                            order=order,
                            product=item["product"],
                            product_name=item["product"].name,
                            price=item["price"],
                            quantity=item["quantity"],
                        )

                    # Razorpay expects the amount in paise.
                    amount_in_paise = int(
                        order.get_total_price()
                        * Decimal("100")
                    )

                    if amount_in_paise <= 0:
                        raise ValueError(
                            "The final order amount must be greater than zero."
                        )

                    razorpay_client = get_razorpay_client()

                    razorpay_order = (
                        razorpay_client.order.create(
                            {
                                "amount": amount_in_paise,
                                "currency": "INR",
                                "receipt": f"order_{order.id}",
                                "notes": {
                                    "local_order_id": str(order.id),
                                    "customer": request.user.username,
                                    "coupon": (
                                        order.coupon_code
                                        if order.coupon_code
                                        else "none"
                                    ),
                                },
                            }
                        )
                    )

                    order.razorpay_order_id = (
                        razorpay_order["id"]
                    )

                    order.save(
                        update_fields=[
                            "razorpay_order_id",
                        ]
                    )

                return redirect(
                    "orders:payment",
                    order_id=order.id,
                )

            except razorpay.errors.BadRequestError as error:
                messages.error(
                    request,
                    f"Unable to create payment: {error}",
                )

            except ValueError as error:
                messages.error(
                    request,
                    str(error),
                )

                return redirect(
                    "cart:cart_detail",
                )

            except Exception:
                messages.error(
                    request,
                    "Unable to begin payment. Please try again.",
                )

    else:
        form = OrderCreateForm(
            initial=initial_data,
        )

    return render(
        request,
        "orders/order_create.html",
        {
            "cart": cart,
            "form": form,
        },
    )


@login_required
def payment_view(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        user=request.user,
    )

    if order.paid:
        return redirect(
            "orders:order_success",
            order_id=order.id,
        )

    if not order.razorpay_order_id:
        messages.error(
            request,
            "Payment order could not be found.",
        )

        return redirect(
            "orders:order_detail",
            order_id=order.id,
        )

    amount_in_paise = int(
        order.get_total_price()
        * Decimal("100")
    )

    context = {
        "order": order,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": order.razorpay_order_id,
        "razorpay_amount": amount_in_paise,
        "razorpay_currency": "INR",
    }

    return render(
        request,
        "payments/payment.html",
        context,
    )


@login_required
@require_POST
def payment_verify(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product",
        ),
        id=order_id,
        user=request.user,
    )

    if order.paid:
        return redirect(
            "orders:order_success",
            order_id=order.id,
        )

    razorpay_payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    razorpay_order_id = request.POST.get(
        "razorpay_order_id"
    )

    razorpay_signature = request.POST.get(
        "razorpay_signature"
    )

    if not all(
        [
            razorpay_payment_id,
            razorpay_order_id,
            razorpay_signature,
        ]
    ):
        messages.error(
            request,
            "Incomplete payment information was received.",
        )

        return redirect(
            "orders:payment",
            order_id=order.id,
        )

    if razorpay_order_id != order.razorpay_order_id:
        messages.error(
            request,
            "The payment order does not match.",
        )

        return redirect(
            "orders:payment",
            order_id=order.id,
        )

    razorpay_client = get_razorpay_client()

    verification_data = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    }

    try:
        razorpay_client.utility.verify_payment_signature(
            verification_data
        )

        with transaction.atomic():
            locked_order = (
                Order.objects
                .select_for_update()
                .prefetch_related("items")
                .get(id=order.id)
            )

            # Prevent duplicate stock reduction and coupon counting.
            if locked_order.paid:
                return redirect(
                    "orders:order_success",
                    order_id=locked_order.id,
                )

            # Validate and reduce stock after verified payment.
            for order_item in locked_order.items.all():
                product = (
                    Product.objects
                    .select_for_update()
                    .get(id=order_item.product_id)
                )

                if not product.is_available:
                    raise ValueError(
                        f"{product.name} is no longer available."
                    )

                if order_item.quantity > product.stock:
                    raise ValueError(
                        f"Insufficient stock for {product.name}."
                    )

                product.stock -= order_item.quantity

                if product.stock == 0:
                    product.is_available = False

                product.save(
                    update_fields=[
                        "stock",
                        "is_available",
                    ]
                )

            # Count coupon usage only after verified payment.
            if locked_order.coupon_id:
                coupon = (
                    Coupon.objects
                    .select_for_update()
                    .get(id=locked_order.coupon_id)
                )

                if not coupon.is_usage_available():
                    raise ValueError(
                        "The coupon usage limit has been reached."
                    )

                coupon.used_count += 1

                coupon.save(
                    update_fields=[
                        "used_count",
                    ]
                )

            locked_order.razorpay_payment_id = (
                razorpay_payment_id
            )

            locked_order.razorpay_signature = (
                razorpay_signature
            )

            locked_order.paid = True
            locked_order.status = Order.Status.CONFIRMED

            locked_order.save(
                update_fields=[
                    "razorpay_payment_id",
                    "razorpay_signature",
                    "paid",
                    "status",
                    "updated_at",
                ]
            )

            Cart(request).clear()

        # Send email only after the database transaction succeeds.
        email_sent = send_order_confirmation_email(
            locked_order,
        )

        if email_sent:
            messages.success(
                request,
                "Payment successful. Your confirmation email has been sent.",
            )
        else:
            messages.warning(
                request,
                "Payment was successful, but the confirmation email could not be sent.",
            )

        return redirect(
            "orders:order_success",
            order_id=locked_order.id,
        )

    except SignatureVerificationError:
        messages.error(
            request,
            "Payment verification failed.",
        )

        return redirect(
            "orders:payment",
            order_id=order.id,
        )

    except ValueError as error:
        messages.error(
            request,
            str(error),
        )

        return redirect(
            "orders:order_detail",
            order_id=order.id,
        )

    except Exception:
        messages.error(
            request,
            "The payment could not be verified.",
        )

        return redirect(
            "orders:payment",
            order_id=order.id,
        )


@login_required
def order_success(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        user=request.user,
        paid=True,
    )

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
        },
    )


@login_required
def order_history(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .select_related("coupon")
        .prefetch_related("items")
    )

    return render(
        request,
        "orders/order_history.html",
        {
            "orders": orders,
        },
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects
        .select_related("coupon")
        .prefetch_related(
            "items__product",
        ),
        id=order_id,
        user=request.user,
    )

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
        },
    )


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(
        Order.objects
        .select_related("coupon")
        .prefetch_related("items"),
        id=order_id,
        user=request.user,
        paid=True,
    )

    pdf_buffer = generate_invoice_pdf(order)

    filename = f"shopsphere-invoice-{order.id}.pdf"

    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )