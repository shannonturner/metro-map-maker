from django import template
from map_saver.models import SavedMap

register = template.Library()

@register.filter(name='existing_maps')
def existing_maps(value, arg):

    """ Use to find existing maps with the same name as this
        that are publicly visible and have some tag
    """

    return SavedMap.objects.filter(**{
        'publicly_visible': True,
        # user-named maps have suggested tags in parentheses,
        # we don't want these considered part of the name
        'name': value.name.split("(")[0],
        'tags__slug': arg,
    }).count()
