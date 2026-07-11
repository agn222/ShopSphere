from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path(
        "register/",
        views.register_view,
        name="register",
    ),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),

    path(
    "logout/",
    views.logout_view,
    name="logout",
),

    path(
        "profile/",
        views.profile_view,
        name="profile",
    ),
    path(
    "wishlist/",
    views.wishlist_view,
    name="wishlist",
),

path(
    "wishlist/add/<int:product_id>/",
    views.wishlist_add,
    name="wishlist_add",
),

path(
    "wishlist/remove/<int:product_id>/",
    views.wishlist_remove,
    name="wishlist_remove",
),
]