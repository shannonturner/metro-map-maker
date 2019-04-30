from map_saver.models import SavedMap

from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User, Permission

class AdminPermissionsTestCase(TestCase):

    def setUp(self):

        """ Create a map and a user
        """

        saved_map = SavedMap(**{
            'urlhash': 'abc123',
            'mapdata': '{"global": {"lines": {"0896d7": {"displayName": "Blue Line"}}}, "1": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}, "2": {"1": {"line": "0896d7"}}, "3": {"1": {"line": "0896d7"}}, "4": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}}'
        })
        saved_map.save()

        test_user = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user.save()

    def test_redirect_if_not_logged_in(self):

        """ Confirm that if you are not logged in,
            a request to one of these will result in a redirect to the login page
        """

        client = Client()

        admin_only_pages = (
            '/admin/gallery/',
            '/admin/gallery/?page=2',
            '/admin/gallery/real/',
            '/admin/gallery/real/?page=2',
            '/admin/similar/abc123',
            '/admin/direct/https://metromapmaker.com/?map=abc123',
        )

        for admin_only_page in admin_only_pages:
            response = client.get(admin_only_page)
            self.assertEqual(response.status_code, 302, admin_only_page)
            self.assertTrue(response.url.startswith('/accounts/login/'), response.url)

        response = client.post('/admin/action/', {'action': 'hide', 'map': 1})
        self.assertEqual(response.status_code, 302, admin_only_page)
        self.assertTrue(response.url.startswith('/accounts/login/'), response.url)

    def test_admin_permission_denied(self):

        """ Confirm that a logged-in user without the proper permissions
            cannot change the objects
        """

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = SavedMap.objects.get(urlhash='abc123')

        self.assertTrue(saved_map.gallery_visible)
        client.post('/admin/action/', {
            'action': 'hide',
            'map': saved_map.id
        })
        # Unchanged, because user did not have permission to hide
        saved_map.refresh_from_db()
        self.assertTrue(saved_map.gallery_visible)

        self.assertEqual(0, saved_map.tags.count())
        client.post('/admin/action/', {
            'action': 'addtag',
            'map': saved_map.id,
            'tag': 'real'
        })
        saved_map.refresh_from_db()
        self.assertEqual(0, saved_map.tags.count())

        self.assertEqual('', saved_map.name)
        client.post('/admin/action/', {
            'action': 'name',
            'map': saved_map.id,
            'name': 'London'
        })
        saved_map.refresh_from_db()
        self.assertEqual('', saved_map.name)

        self.assertEqual('', saved_map.thumbnail)
        client.post('/admin/action/', {
            'action': 'thumbnail',
            'map': saved_map.id,
            'data': 'thumbnail data'
        })
        saved_map.refresh_from_db()
        self.assertEqual('', saved_map.thumbnail)

    def test_admin_permission_granted_hide_map(self):

        """ Confirm that a logged-in user with the proper permissions
            can hide a map
        """

        permission = Permission.objects.get(name="Can set a map's gallery_visible to hidden")
        test_user = User.objects.get(username='testuser1')
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = SavedMap.objects.get(urlhash='abc123')

        self.assertTrue(saved_map.gallery_visible)
        response = client.post('/admin/action/', {
            'action': 'hide',
            'map': saved_map.id
        })
        saved_map.refresh_from_db()
        self.assertFalse(saved_map.gallery_visible, response.context['status'])

    def test_admin_permission_granted_add_tag(self):

        """ Confirm that a logged-in user with the proper permissions
            can tag a map
        """

        permission = Permission.objects.get(name="Can change the tags associated with a map")
        test_user = User.objects.get(username='testuser1')
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = SavedMap.objects.get(urlhash='abc123')

        self.assertEqual(0, saved_map.tags.count())
        response = client.post('/admin/action/', {
            'action': 'addtag',
            'map': saved_map.id,
            'tag': 'real'
        })
        saved_map.refresh_from_db()
        self.assertEqual(1, saved_map.tags.count())

    def test_admin_permission_granted_name_map(self):

        """ Confirm that a logged-in user with the proper permissions
            can name a map
        """

        permission = Permission.objects.get(name="Can set a map's name")
        test_user = User.objects.get(username='testuser1')
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = SavedMap.objects.get(urlhash='abc123')

        self.assertEqual('', saved_map.name)
        client.post('/admin/action/', {
            'action': 'name',
            'map': saved_map.id,
            'name': 'London'
        })
        saved_map.refresh_from_db()
        self.assertEqual('London', saved_map.name)

    def test_admin_permission_granted_generate_thumbnail(self):

        """ Confirm that a logged-in user with the proper permissions
            can name a map
        """

        permission = Permission.objects.get(name="Can generate thumbnails for a map")
        test_user = User.objects.get(username='testuser1')
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = SavedMap.objects.get(urlhash='abc123')

        self.assertEqual('', saved_map.thumbnail)
        client.post('/admin/action/', {
            'action': 'thumbnail',
            'map': saved_map.id,
            'data': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHgAAAB4CAYAAAA5ZDbSAAACB0lEQVR4Xu3VwVGDYBgG4Y9KpJOklFiJWolaibGSYCU40YPjOBaQnYcLHNnd/4Vl3/f9/rzNbDOzzmzbzLrOHNaZ0/XBddMGltPbZX95v9b9e+0Px5uG8/IzvwIf79Y5f/zEFvj2j8jyfLns96/bPB7WeTh+f5KXp/PXXeBA4Os/+PYxEPxnYBG4fTgEbvcdgQWOG4jjWbDAcQNxPAsWOG4gjmfBAscNxPEsWOC4gTieBQscNxDHs2CB4wbieBYscNxAHM+CBY4biONZsMBxA3E8CxY4biCOZ8ECxw3E8SxY4LiBOJ4FCxw3EMezYIHjBuJ4Fixw3EAcz4IFjhuI41mwwHEDcTwLFjhuII5nwQLHDcTxLFjguIE4ngULHDcQx7NggeMG4ngWLHDcQBzPggWOG4jjWbDAcQNxPAsWOG4gjmfBAscNxPEsWOC4gTieBQscNxDHs2CB4wbieBYscNxAHM+CBY4biONZsMBxA3E8CxY4biCOZ8ECxw3E8SxY4LiBOJ4FCxw3EMezYIHjBuJ4Fixw3EAcz4IFjhuI41mwwHEDcTwLFjhuII5nwQLHDcTxLFjguIE4ngULHDcQx7NggeMG4ngWLHDcQBzPggWOG4jjWbDAcQNxPAsWOG4gjmfBAscNxPEsWOC4gTieBQscNxDHs2CB4wbieBYscNxAHM+C44E/Aa8c86hmtT50AAAAAElFTkSuQmCC'
        })
        saved_map.refresh_from_db()
        self.assertTrue(saved_map.thumbnail)
