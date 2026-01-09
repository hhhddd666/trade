# utils/pdf_generator.py
import pdfkit
from django.template.loader import render_to_string
from django.conf import settings
import os

def generate_contract_pdf(contract_data, output_path):
    """
    生成合同PDF
    """
    html_content = render_to_string('contract_template.html', contract_data)

    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None
    }

    pdfkit.from_string(html_content, output_path, options=options)
