from django import template

register = template.Library()

@register.filter
def subtract(value1, value2):
    return value1 - value2

@register.filter    
def first(value):
    return value.split()[0]

@register.filter(name='to_integer')    
def to_integer(value):
    return int(value)