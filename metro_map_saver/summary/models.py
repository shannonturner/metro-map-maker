from django.db import models

# Create your models here.

class MapsByDay(models.Model):

    """ How many maps were created on each day,
            with the caveat that the created_at field
            was added roughly a year after launch (sigh)
    """

    day = models.DateField()
    maps = models.IntegerField()

    def __str__(self):
        return f'{self.day}: {self.maps}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['day'], name='unique_mapsbyday_day'),
        ]

class MapsByCity(models.Model):

    """ How many maps were created by city,
            plus one map that's featured
    """

    city = models.ForeignKey('map_saver.City', on_delete=models.CASCADE)
    maps = models.IntegerField(null=True)
    featured = models.ForeignKey('map_saver.SavedMap', null=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['city'], name='unique_mapsbycity_city'),
        ]

    def __str__(self):
        return self.city.name
