from django import template
from ..models import EMPLOYMENT_TYPE

register = template.Library()

@register.filter
def add_plus_sign(value):
    return value.replace(' ','+')

@register.filter
def display_name(q):
    return dict(EMPLOYMENT_TYPE).get(q)