from django.db import models
from django.contrib.auth.models import User

from map_saver.models import SavedMap

class ActivityLog(models.Model):

    """ Log of every admin action taken on a SavedMap
    """

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    savedmap = models.ForeignKey(SavedMap, on_delete=models.PROTECT)
    action = models.CharField(max_length=255, blank=True, default='')
    details = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"ActivityLog: {self.user} {self.action} {self.savedmap}"

# Possible ideas to implement
# class AuthUserRestrictions(models.Model):

#     """ A set of finer-grained access restrictions
#         on changing a map
#         beyond the permissions structure
#     """

#     user = models.ForeignKey(User)

#     # Can't edit anything below minimum_savedmap_id
#     #   or above maximum_savedmap_id
#     minimum_savedmap_id = models.IntegerField(default=0)
#     maximum_savedmap_id = models.IntegerField(default=0)

#     # Can't edit anything with these tags
#     forbidden_tags = ...

#     # Can't edit anything a superuser has edited
#     ...
