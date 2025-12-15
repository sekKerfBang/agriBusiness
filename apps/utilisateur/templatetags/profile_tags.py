from django import template

register = template.Library()

@register.filter(name='get_icon')
def get_icon(field_name):
    """Retourne une icône Font Awesome selon le nom du champ"""
    icons = {
        'phone': 'phone',
        'location': 'map-marker-alt',
        'email': 'envelope',
        'password': 'key',
        'confirm_password': 'key',
        'is_organic': 'leaf',
        'description': 'align-left',
        'certifications': 'certificate',
    }
    return icons.get(field_name, 'circle')