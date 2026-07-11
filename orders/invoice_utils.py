from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def format_money(value):
    """
    Use INR instead of the ₹ symbol because ReportLab's
    built-in Helvetica font may not contain that symbol.
    """
    return f"INR {value:.2f}"


def generate_invoice_pdf(order):
    """
    Generate an invoice PDF in memory and return its BytesIO buffer.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"ShopSphere Invoice #{order.id}",
        author="ShopSphere",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "InvoiceSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceBefore=12,
        spaceAfter=8,
    )

    right_style = ParagraphStyle(
        "RightAligned",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    )

    story = []

    # Header
    story.append(
        Paragraph(
            "ShopSphere",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Payment Invoice",
            subtitle_style,
        )
    )

    invoice_information = [
        [
            Paragraph("<b>Invoice number</b>", styles["Normal"]),
            Paragraph(f"INV-{order.id:06d}", right_style),
        ],
        [
            Paragraph("<b>Order number</b>", styles["Normal"]),
            Paragraph(f"#{order.id}", right_style),
        ],
        [
            Paragraph("<b>Invoice date</b>", styles["Normal"]),
            Paragraph(
                order.created_at.strftime("%d %B %Y"),
                right_style,
            ),
        ],
        [
            Paragraph("<b>Payment status</b>", styles["Normal"]),
            Paragraph(
                "PAID" if order.paid else "PENDING",
                right_style,
            ),
        ],
        [
            Paragraph("<b>Order status</b>", styles["Normal"]),
            Paragraph(
                escape(order.get_status_display()),
                right_style,
            ),
        ],
    ]

    information_table = Table(
        invoice_information,
        colWidths=[80 * mm, 80 * mm],
    )

    information_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(information_table)
    story.append(Spacer(1, 14))

    # Customer information
    story.append(
        Paragraph(
            "Customer and Delivery Information",
            section_style,
        )
    )

    customer_name = escape(
        f"{order.first_name} {order.last_name}".strip()
    )

    address_parts = [
        escape(order.address_line_1),
    ]

    if order.address_line_2:
        address_parts.append(
            escape(order.address_line_2)
        )

    address_parts.extend(
        [
            escape(f"{order.city}, {order.state}"),
            escape(f"{order.postal_code}, {order.country}"),
        ]
    )

    customer_information = [
        [
            Paragraph("<b>Customer</b>", styles["Normal"]),
            Paragraph(customer_name, styles["Normal"]),
        ],
        [
            Paragraph("<b>Email</b>", styles["Normal"]),
            Paragraph(escape(order.email), styles["Normal"]),
        ],
        [
            Paragraph("<b>Phone</b>", styles["Normal"]),
            Paragraph(escape(order.phone_number), styles["Normal"]),
        ],
        [
            Paragraph("<b>Address</b>", styles["Normal"]),
            Paragraph("<br/>".join(address_parts), styles["Normal"]),
        ],
    ]

    customer_table = Table(
        customer_information,
        colWidths=[42 * mm, 118 * mm],
    )

    customer_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(customer_table)
    story.append(Spacer(1, 14))

    # Order items
    story.append(
        Paragraph(
            "Order Items",
            section_style,
        )
    )

    item_data = [
        [
            Paragraph("<b>Product</b>", styles["Normal"]),
            Paragraph("<b>Price</b>", right_style),
            Paragraph("<b>Quantity</b>", right_style),
            Paragraph("<b>Total</b>", right_style),
        ]
    ]

    for item in order.items.all():
        item_data.append(
            [
                Paragraph(
                    escape(item.product_name),
                    styles["Normal"],
                ),
                Paragraph(
                    format_money(item.price),
                    right_style,
                ),
                Paragraph(
                    str(item.quantity),
                    right_style,
                ),
                Paragraph(
                    format_money(item.get_cost()),
                    right_style,
                ),
            ]
        )

    items_table = Table(
        item_data,
        colWidths=[
            75 * mm,
            32 * mm,
            23 * mm,
            35 * mm,
        ],
        repeatRows=1,
    )

    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#f9fafb"),
                ]),
            ]
        )
    )

    story.append(items_table)
    story.append(Spacer(1, 14))

    # Totals
    totals_data = [
        [
            Paragraph("Subtotal", styles["Normal"]),
            Paragraph(
                format_money(order.get_subtotal()),
                right_style,
            ),
        ]
    ]

    if order.discount > 0:
        coupon_label = "Discount"

        if order.coupon_code:
            coupon_label = (
                f"Coupon ({escape(order.coupon_code)})"
            )

        totals_data.append(
            [
                Paragraph(
                    coupon_label,
                    styles["Normal"],
                ),
                Paragraph(
                    f"- {format_money(order.discount)}",
                    right_style,
                ),
            ]
        )

    totals_data.append(
        [
            Paragraph(
                "<b>Total Paid</b>",
                styles["Normal"],
            ),
            Paragraph(
                f"<b>{format_money(order.get_total_price())}</b>",
                right_style,
            ),
        ]
    )

    totals_table = Table(
        totals_data,
        colWidths=[115 * mm, 50 * mm],
        hAlign="RIGHT",
    )

    totals_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dbeafe")),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor("#1d4ed8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )

    story.append(totals_table)
    story.append(Spacer(1, 24))

    story.append(
        Paragraph(
            "Thank you for shopping with ShopSphere.",
            ParagraphStyle(
                "ThankYou",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                fontSize=11,
                textColor=colors.HexColor("#6b7280"),
            ),
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer