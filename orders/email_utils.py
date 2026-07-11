import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def send_order_confirmation_email(order) -> bool:
    """
    Send the paid-order confirmation email.

    Returns True when Django successfully hands the email
    to the configured email backend; otherwise returns False.
    """

    if not order.email:
        logger.warning(
            "Order %s has no customer email address.",
            order.id,
        )
        return False

    context = {
        "order": order,
        "items": order.items.select_related("product").all(),
    }

    subject = f"Order Confirmation - ShopSphere #{order.id}"

    text_body = render_to_string(
        "emails/order_confirmation.txt",
        context,
    )

    html_body = render_to_string(
        "emails/order_confirmation.html",
        context,
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )

    email.attach_alternative(
        html_body,
        "text/html",
    )

    try:
        sent_count = email.send(fail_silently=False)
        return sent_count == 1

    except Exception:
        logger.exception(
            "Could not send confirmation email for order %s.",
            order.id,
        )
        return False