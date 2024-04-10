from django import template

register = template.Library()

@register.filter()
def access_list(value, arg):

    """ Django's built-in |slice doesn't give a single result
        because it's assumed you'd use dot accessors,
        but those won't work for variables.
    """

    return value[arg]
