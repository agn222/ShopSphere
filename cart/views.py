from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from store.models import Product

from .cart import Cart
from .forms import CartAddProductForm


def cart_detail(request):
    cart = Cart(request)

    for item in cart:
        item["update_quantity_form"] = CartAddProductForm(
            initial={
                "quantity": item["quantity"],
                "override": True,
            }
        )

    return render(
        request,
        "cart/cart_detail.html",
        {
            "cart": cart,
        },
    )


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cleaned_data = form.cleaned_data

        quantity = cleaned_data["quantity"]
        override = cleaned_data["override"]

        if quantity > product.stock:
            messages.error(
                request,
                f"Only {product.stock} item(s) available.",
            )
        else:
            cart.add(
                product=product,
                quantity=quantity,
                override_quantity=override,
            )

            messages.success(
                request,
                f"{product.name} added to cart.",
            )

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    cart.remove(product)

    messages.success(
        request,
        f"{product.name} removed from cart.",
    )

    return redirect("cart:cart_detail")