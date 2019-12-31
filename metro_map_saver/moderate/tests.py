from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User, Permission

from map_saver.models import SavedMap

class ModeratePermissionsTestCase(TestCase):

    def setUp(self):

        self.saved_map = SavedMap(**{
            'urlhash': 'abcd1234',
            'mapdata': '{"global": {"lines": {"0896d7": {"displayName": "Blue Line"}}}, "1": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}, "2": {"1": {"line": "0896d7"}}, "3": {"1": {"line": "0896d7"}}, "4": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}}'
        })
        self.saved_map.save()

        self.test_user = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        self.test_user.save()

    def test_only_own_activity_log(self):

        """ Confirm that you can only view your own activity log,
            nobody else's, and not the main log of everyone's activity
        """

        # Create a user who is trying to be sneaky
        snoop_user = User.objects.create_user(username='snoop', password='dogg')
        snoop_user.save()

        client = Client()
        client.login(username='snoop', password='dogg')

        # Not allowed to view the main log
        response = client.get('/admin/activity/', follow=True)
        self.assertEqual(response.status_code, 403)

        # Not allowed to view someone else's log
        response = client.get(f'/admin/activity/{self.test_user.id}')
        self.assertEqual(response.status_code, 403)

        # Not allowed to view a map directly, either
        response = client.get(f'/admin/activity/{self.saved_map.urlhash}')
        self.assertEqual(response.status_code, 403)

        # But allowed to view my own log
        response = client.get(f'/admin/activity/{snoop_user.id}')
        self.assertEqual(response.status_code, 200)
