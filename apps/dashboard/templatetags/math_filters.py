# apps/dashboard/templatetags/math_filters.py
from django import template
import builtins

register = template.Library()

@register.filter
def abs(value):
    """Retourne la valeur absolue"""
    try:
        return builtins.abs(value)
    except:
        return value

@register.filter
def positive(value):
    """Retourne la valeur absolue (pour affichage positif)"""
    return abs(value)

@register.filter
def percentage(value, total):
    """Retourne value / total * 100 avec 1 décimale"""
    try:
        return round((value / total) * 100, 1) if total else 0
    except:
        return 0
    
@register.filter
def divide(value, divisor):
    """Retourne value divisé par divisor"""
    try:
        return value / divisor if divisor else 0
    except:
        return 0
@register.filter
def multiply(value, factor):
    """Retourne value multiplié par factor"""
    try:
        return value * factor
    except:
        return 0

@register.filter
def subtract(value, subtrahend):
    """Retourne value moins subtrahend"""
    try:
        return value - subtrahend
    except:
        return value

@register.filter
def add(value, addend): 
    """Retourne value plus addend"""
    try:
        return value + addend
    except:
        return value

@register.filter
def floatformat(value, decimal_places=2):
    """Retourne la valeur formatée en float avec decimal_places décimales"""
    try:
        return f"{float(value):.{decimal_places}f}"
    except:
        return value

@register.filter
def round_value(value, decimal_places=0):
    """Retourne la valeur arrondie à decimal_places décimales"""
    try:
        return round(float(value), decimal_places)
    except:
        return value

@register.filter
def to_int(value):
    """Convertit la valeur en entier"""
    try:
        return int(value)
    except:
        return value        
                        