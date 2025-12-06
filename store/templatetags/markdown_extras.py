import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdown')
def markdown_filter(text):
    """Convert markdown text to HTML with tables extension"""
    if not text:
        return ''
    
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'nl2br',
        'sane_lists',
    ])
    
    return mark_safe(md.convert(text))
