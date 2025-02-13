from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retrieve a value from a dictionary given its key."""
    return dictionary.get(key, 0)
