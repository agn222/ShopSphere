from django.urls import path

from . import views


app_name = "orders"


urlpatterns = [
    path(
        "checkout/",
        views.order_create,
        name="order_create",
    ),

    path(
        "<int:order_id>/payment/",
        views.payment_view,
        name="payment",
    ),

    path(
        "<int:order_id>/payment/verify/",
        views.payment_verify,
        name="payment_verify",
    ),

    path(
        "success/<int:order_id>/",
        views.order_success,
        name="order_success",
    ),

    path(
        "history/",
        views.order_history,
        name="order_history",
    ),
    path(
    "<int:order_id>/invoice/",
    views.download_invoice,
    name="download_invoice",
),

    path(
        "<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),
]