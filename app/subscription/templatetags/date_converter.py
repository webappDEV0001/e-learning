import datetime
from django import template

register = template.Library()

@register.filter
def datetime_converter(value):
    """convert int to datetime"""
    return datetime.datetime.fromtimestamp(value).strftime("%d-%m-%Y")


@register.filter
def datetime_format(value):
    """convert int to datetime"""
    return value.strftime("%d-%m-%Y")
