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
