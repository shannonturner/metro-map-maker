from map_saver.models import SavedMap

from django.test import Client
from django.test import TestCase

class SavedMapTest(TestCase):

    def setUp(self):

        """ Create a map
        """

        self.saved_map = SavedMap(**{
            'urlhash': 'abc123',
            'mapdata': '{"global": {"lines": {"0896d7": {"displayName": "Blue Line"}}}, "1": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}, "2": {"1": {"line": "0896d7"}}, "3": {"1": {"line": "0896d7"}}, "4": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}}'
        })
        self.saved_map.save()

    def test_publicly_visible(self):

        """ Confirm that a map is only publicly visible
            when ALL of the following conditions are met:

                .gallery_visible = True
                .name is not blank
                .thumbnail is not blank
                and it has at least one tag in PUBLICLY_VISIBLE_TAGS

            If any of those conditions stop being true,
            the map should stop being publicly visible upon .save()
        """

        client = Client()

        assignments = {
            'gallery_visible': True,
            'name': 'Cool Map',
            'thumbnail': 'Thumbnail',
        }

        self.assertFalse(self.saved_map.publicly_visible)
        response = client.get('/gallery/')
        self.assertNotContains(response, 'Cool Map')

        # Even after all of these, I still don't have the tag
        for key, value in assignments.items():
            setattr(self.saved_map, key, value)
            self.saved_map.save()
            self.saved_map.refresh_from_db()
            self.assertFalse(self.saved_map.publicly_visible)

        self.saved_map.tags.add('irrelevant')
        self.saved_map.save()
        self.saved_map.refresh_from_db()
        self.assertFalse(self.saved_map.publicly_visible)

        # This tag is good, so now my map is finally publicly visible
        self.saved_map.tags.add('real')
        self.saved_map.save()
        self.saved_map.refresh_from_db()
        self.assertTrue(self.saved_map.publicly_visible)

        # And it will appear in the 'real' section of the public gallery
        response = client.get('/gallery/')
        self.assertContains(response, 'Cool Map')

        # Any of these is sufficient to make the map no longer publicly visible
        negative_assignments = {
            'gallery_visible': False,
            'name': ' ',
            'thumbnail': ' ',
        }
        for key, value in negative_assignments.items():
            setattr(self.saved_map, key, value)
            self.saved_map.save()
            self.saved_map.refresh_from_db()
            self.assertFalse(self.saved_map.publicly_visible)
            response = client.get('/gallery/')
            self.assertNotContains(response, 'Cool Map')

            # But let's put it back the way it was and confirm we're visible again
            setattr(self.saved_map, key, assignments[key])
            self.saved_map.save()
            self.saved_map.refresh_from_db()
            self.assertTrue(self.saved_map.publicly_visible)
            response = client.get('/gallery/')
            self.assertContains(response, 'Cool Map')

        # Finally, remove the tag and confirm it's no longer visible
        self.saved_map.tags.remove('real')
        self.saved_map.save()
        self.saved_map.refresh_from_db()
        self.assertFalse(self.saved_map.publicly_visible)
        response = client.get('/gallery/')
        self.assertNotContains(response, 'Cool Map')
