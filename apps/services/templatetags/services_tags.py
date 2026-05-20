from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Access dictionary by key in templates: dict|get_item:key"""
    if dictionary is None:
        return []
    return dictionary.get(key, [])
