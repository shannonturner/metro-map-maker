from django import template

register = template.Library()

@register.simple_tag()
def map_count_by_month(counts_by_month, month):

    """ Django seems confused that I want to use 
        the forloop.counter to access the value of a list,        
        and |slice is giving me more than one result
    """

    return f'{counts_by_month.get(month, 0):,}'
