from io import BytesIO
from typing import Dict, List

from reportlab.pdfgen import canvas
from django.http import HttpResponse


def pdf_shopping_cart(items: List[Dict]) -> HttpResponse:
    result = HttpResponse(content_type="application/pdf")
    result["Content-Disposition"] = 'attachment; filename="shopping_list.pdf"'
    stream = BytesIO()
    canvas_obj = canvas.Canvas(stream)
    canvas_obj.setFont("Helvetica", 12)
    canvas_obj.drawString(220, 800, "Ваш список покупок")

    vertical_position = 750
    spacing = 20

    for idx, entry in enumerate(items, 1):
        content = (
            f'{idx}) {entry["ingredient__name"]} - '
            f'{entry["ingredient_value"]} '
            f'{entry["ingredient__measurement_unit"]}'
        )
        canvas_obj.drawString(60, vertical_position, content)
        vertical_position -= spacing
        if vertical_position < 60:
            canvas_obj.showPage()
            canvas_obj.setFont("Helvetica", 12)
            vertical_position = 750

    canvas_obj.save()
    stream.seek(0)
    result.write(stream.read())
    stream.close()
    return result
