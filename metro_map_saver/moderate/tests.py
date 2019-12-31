from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User, Permission

class ModeratePermissionsTestCase(TestCase):

    def setUp(self):

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

        # But allowed to view my own log
        response = client.get(f'/admin/activity/{snoop_user.id}')
        self.assertEqual(response.status_code, 200)
