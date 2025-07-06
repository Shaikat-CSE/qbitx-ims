import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
    """
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(result)[0]
        if result.endswith(('.png', '.jpg', '.jpeg')):
            path = result
        else:
            path = result
        return path
    return uri


def render_to_pdf(template_src, context_dict={}):
    """
    Render HTML template to PDF
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    pdf_status = pisa.CreatePDF(
        html, dest=response, link_callback=link_callback)
    
    if pdf_status.err:
        return HttpResponse('We had some errors with code %s' % pdf_status.err)
    
    return response 