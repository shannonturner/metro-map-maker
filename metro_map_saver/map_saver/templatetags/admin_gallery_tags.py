from django import template
from map_saver.models import SavedMap

register = template.Library()

@register.filter(name='existing_maps')
def existing_maps(value, arg):

    """ Use to find existing maps with the same name as this
        that are publicly visible and have some tag
    """
    # user-named maps have suggested tags in parentheses,
    #   and TravelSystems contain the country name (after a comma)
    # we don't want these considered part of the name
    name = value.name.split("(")[0].strip()
    name = name.split(",")[0].strip()
    return SavedMap.objects.filter(**{
        'publicly_visible': True,
        'name': name,
        'tags__slug': arg,
    }).count()

@register.simple_tag(name='find_existing_maps')
def existing_maps_search_by_name_tag(name, tag):

    """ Use to find existing publicly visible maps,
        searching by name and tag
    """
    name = name.split("(")[0].strip()
    name = name.split(",")[0].strip()
    if name:
        return SavedMap.objects.filter(**{
            'publicly_visible': True,
            'name__contains': name,
            'tags__slug': tag,
        }).count()
