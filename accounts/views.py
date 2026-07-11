from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from store.models import Product

from .models import Profile, Wishlist

from .forms import ProfileForm, RegisterForm, UserUpdateForm
from .models import Profile, Wishlist


def register_view(request):
    if request.user.is_authenticated:
        return redirect("store:product_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Your account was created successfully.",
            )

            return redirect("accounts:profile")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":
        user_form = UserUpdateForm(
            request.POST,
            instance=request.user,
        )

        profile_form = ProfileForm(
            request.POST,
            instance=profile,
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            messages.success(
                request,
                "Your profile was updated successfully.",
            )

            return redirect("accounts:profile")

    else:
        user_form = UserUpdateForm(
            instance=request.user,
        )

        profile_form = ProfileForm(
            instance=profile,
        )

    return render(
        request,
        "accounts/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )

from django.views.decorators.http import require_POST


@require_POST
def logout_view(request):
    # Save cart data before Django clears the session
    saved_cart = request.session.get("cart", {}).copy()

    # Logout flushes the current session
    logout(request)

    # Restore the cart into the new anonymous session
    if saved_cart:
        request.session["cart"] = saved_cart
        request.session.modified = True

    messages.success(
        request,
        "You have been logged out successfully.",
    )

    return redirect("store:product_list")

@login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user,
    )

    products = (
        wishlist.products
        .filter(is_available=True)
        .select_related("category")
        .order_by("-created_at")
    )

    return render(
        request,
        "accounts/wishlist.html",
        {
            "wishlist": wishlist,
            "products": products,
        },
    )


@login_required
@require_POST
def wishlist_add(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user,
    )

    if wishlist.products.filter(id=product.id).exists():
        messages.info(
            request,
            f"{product.name} is already in your wishlist.",
        )
    else:
        wishlist.products.add(product)

        messages.success(
            request,
            f"{product.name} added to your wishlist.",
        )

    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("accounts:wishlist")


@login_required
@require_POST
def wishlist_remove(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
    )

    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user,
    )

    wishlist.products.remove(product)

    messages.success(
        request,
        f"{product.name} removed from your wishlist.",
    )

    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("accounts:wishlist")