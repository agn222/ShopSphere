from django.shortcuts import get_object_or_404, render

from cart.forms import CartAddProductForm

from .models import Category, Product

from django.core.paginator import Paginator
from django.db.models import Q


from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.forms import CartAddProductForm

from .forms import ReviewForm
from .models import Category, Product, Review


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()

    products = (
        Product.objects
        .filter(is_available=True)
        .select_related("category")
    )

    # Category filter
    if category_slug:
        category = get_object_or_404(
            Category,
            slug=category_slug,
        )

        products = products.filter(
            category=category,
        )

    # Read query parameters
    search_query = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "")
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    availability = request.GET.get("availability", "")

    # Search
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    # Minimum price
    if min_price:
        try:
            minimum = Decimal(min_price)

            if minimum >= 0:
                products = products.filter(
                    price__gte=minimum,
                )
        except InvalidOperation:
            min_price = ""

    # Maximum price
    if max_price:
        try:
            maximum = Decimal(max_price)

            if maximum >= 0:
                products = products.filter(
                    price__lte=maximum,
                )
        except InvalidOperation:
            max_price = ""

    # Availability
    if availability == "in_stock":
        products = products.filter(
            stock__gt=0,
        )

    elif availability == "out_of_stock":
        products = products.filter(
            stock=0,
        )

    # Sorting
    sorting_options = {
        "newest": "-created_at",
        "oldest": "created_at",
        "price_low": "price",
        "price_high": "-price",
        "name_az": "name",
        "name_za": "-name",
    }

    products = products.order_by(
        sorting_options.get(sort, "-created_at")
    )

    # Pagination
    paginator = Paginator(
        products,
        9,
    )

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Keep all filters when moving between pages
    query_params = request.GET.copy()

    if "page" in query_params:
        query_params.pop("page")

    context = {
        "category": category,
        "categories": categories,
        "products": page_obj,
        "page_obj": page_obj,
        "search_query": search_query,
        "selected_sort": sort,
        "min_price": min_price,
        "max_price": max_price,
        "availability": availability,
        "query_string": query_params.urlencode(),
    }

    return render(
        request,
        "store/product_list.html",
        context,
    )


def product_detail(request, product_slug):
    product = get_object_or_404(
        Product.objects.select_related("category"),
        slug=product_slug,
        is_available=True,
    )

    reviews = (
        product.reviews
        .select_related("user")
        .all()
    )

    user_review = None

    if request.user.is_authenticated:
        user_review = Review.objects.filter(
            product=product,
            user=request.user,
        ).first()

    review_form = ReviewForm(
        instance=user_review,
    )

    cart_product_form = CartAddProductForm()

    context = {
        "product": product,
        "reviews": reviews,
        "user_review": user_review,
        "review_form": review_form,
        "cart_product_form": cart_product_form,
    }

    return render(
        request,
        "store/product_detail.html",
        context,
    )

@login_required
@require_POST
def review_save(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    existing_review = Review.objects.filter(
        product=product,
        user=request.user,
    ).first()

    form = ReviewForm(
        request.POST,
        instance=existing_review,
    )

    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()

        if existing_review:
            messages.success(
                request,
                "Your review was updated successfully.",
            )
        else:
            messages.success(
                request,
                "Your review was submitted successfully.",
            )
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)

    return redirect(product.get_absolute_url())


@login_required
@require_POST
def review_delete(request, review_id):
    review = get_object_or_404(
        Review,
        id=review_id,
        user=request.user,
    )

    product_url = review.product.get_absolute_url()

    review.delete()

    messages.success(
        request,
        "Your review was deleted.",
    )

    return redirect(product_url)