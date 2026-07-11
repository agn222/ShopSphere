from django.urls import path

from . import views


app_name = "store"


urlpatterns = [
    path(
        "",
        views.product_list,
        name="product_list",
    ),

    path(
        "category/<slug:category_slug>/",
        views.product_list,
        name="category_products",
    ),

    path(
        "product/<slug:product_slug>/",
        views.product_detail,
        name="product_detail",
    ),
    path(
    "review/save/<int:product_id>/",
    views.review_save,
    name="review_save",
),

path(
    "review/delete/<int:review_id>/",
    views.review_delete,
    name="review_delete",
),
]