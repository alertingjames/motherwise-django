from django import template

register = template.Library()

@register.filter()
def to_int(value):
    return int(value)


@register.filter
def add( value, arg ):
    try:
        value = int( value )
        arg = int( arg )
        if arg: return value + arg
    except: pass
    return ''


@register.filter
def div( value, arg ):
    try:
        value = int( value )
        arg = int( arg )
        if arg: return value / arg
    except: pass
    return ''