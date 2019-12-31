from map_saver.models import SavedMap

from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User, Permission

class AdminPermissionsTestCase(TestCase):

    def setUp(self):

        """ Create a map and a user
        """

        self.saved_map = SavedMap(**{
            'urlhash': 'abc123',
            'mapdata': '{"global": {"lines": {"0896d7": {"displayName": "Blue Line"}}}, "1": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}, "2": {"1": {"line": "0896d7"}}, "3": {"1": {"line": "0896d7"}}, "4": {"1": {"line": "0896d7"}, "2": {"line": "0896d7"}}}'
        })
        self.saved_map.save()

        self.test_user = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        self.test_user.save()

    def confirm_activity_log(self, action, details=''):

        """ Helper function to confirm that an ActivityLog is created for every entry
        """

        activity_log = self.saved_map.activitylog_set.order_by('-created_at').first()
        self.assertEqual(activity_log.user, self.test_user)
        self.assertEqual(activity_log.savedmap, self.saved_map)
        self.assertEqual(activity_log.action, action)
        self.assertEqual(activity_log.details, details)

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
            '/admin/activity/',
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

        saved_map = self.saved_map

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
        test_user = self.test_user
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = self.saved_map

        action = 'hide'

        self.assertTrue(saved_map.gallery_visible)
        response = client.post('/admin/action/', {
            'action': 'hide',
            'map': saved_map.id
        })
        saved_map.refresh_from_db()
        self.assertFalse(saved_map.gallery_visible, response.context['status'])

        # Confirm there is a record of this action
        self.assertEqual(saved_map.activitylog_set.count(), 1)
        self.confirm_activity_log(action)

        # Hiding the map again will show it
        response = client.post('/admin/action/', {
            'action': 'hide',
            'map': saved_map.id
        })
        saved_map.refresh_from_db()
        self.assertTrue(saved_map.gallery_visible)

        # Confirm there is a record of this action
        self.assertEqual(saved_map.activitylog_set.count(), 2)
        self.confirm_activity_log('show')

    def test_admin_permission_granted_add_tag(self):

        """ Confirm that a logged-in user with the proper permissions
            can tag a map
        """

        permission = Permission.objects.get(name="Can change the tags associated with a map")
        test_user = self.test_user
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = self.saved_map

        action = 'addtag'

        self.assertEqual(0, saved_map.tags.count())
        response = client.post('/admin/action/', {
            'action': action,
            'map': saved_map.id,
            'tag': 'real'
        })
        saved_map.refresh_from_db()
        self.assertEqual(1, saved_map.tags.count())

        # Confirm there is a record of this action
        self.assertEqual(saved_map.activitylog_set.count(), 1)
        self.confirm_activity_log(action, 'real')

        # Remove the tag
        action = 'removetag'
        response = client.post('/admin/action/', {
            'action': action,
            'map': saved_map.id,
            'tag': 'real'
        })
        saved_map.refresh_from_db()
        self.assertEqual(0, saved_map.tags.count())

        # Confirm there is a record of this action
        self.assertEqual(saved_map.activitylog_set.count(), 2)
        self.confirm_activity_log(action, 'real')

    def test_admin_permission_granted_name_map(self):

        """ Confirm that a logged-in user with the proper permissions
            can name a map
        """

        permission = Permission.objects.get(name="Can set a map's name")
        test_user = self.test_user
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = self.saved_map

        action = 'name'

        self.assertEqual('', saved_map.name)
        client.post('/admin/action/', {
            'action': action,
            'map': saved_map.id,
            'name': 'London'
        })
        saved_map.refresh_from_db()
        self.assertEqual('London', saved_map.name)

        # Confirm there is a record of this action
        self.assertEqual(saved_map.activitylog_set.count(), 1)
        self.confirm_activity_log(action, 'London')

    def test_admin_permission_granted_generate_thumbnail(self):

        """ Confirm that a logged-in user with the proper permissions
            can name a map
        """

        permission = Permission.objects.get(name="Can generate thumbnails for a map")
        test_user = self.test_user
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        saved_map = self.saved_map

        action = 'thumbnail'

        self.assertEqual('', saved_map.thumbnail)
        client.post('/admin/action/', {
            'action': 'thumbnail',
            'map': saved_map.id,
            'data': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHgAAAB4CAYAAAA5ZDbSAAACB0lEQVR4Xu3VwVGDYBgG4Y9KpJOklFiJWolaibGSYCU40YPjOBaQnYcLHNnd/4Vl3/f9/rzNbDOzzmzbzLrOHNaZ0/XBddMGltPbZX95v9b9e+0Px5uG8/IzvwIf79Y5f/zEFvj2j8jyfLns96/bPB7WeTh+f5KXp/PXXeBA4Os/+PYxEPxnYBG4fTgEbvcdgQWOG4jjWbDAcQNxPAsWOG4gjmfBAscNxPEsWOC4gTieBQscNxDHs2CB4wbieBYscNxAHM+CBY4biONZsMBxA3E8CxY4biCOZ8ECxw3E8SxY4LiBOJ4FCxw3EMezYIHjBuJ4Fixw3EAcz4IFjhuI41mwwHEDcTwLFjhuII5nwQLHDcTxLFjguIE4ngULHDcQx7NggeMG4ngWLHDcQBzPggWOG4jjWbDAcQNxPAsWOG4gjmfBAscNxPEsWOC4gTieBQscNxDHs2CB4wbieBYscNxAHM+CBY4biONZsMBxA3E8CxY4biCOZ8ECxw3E8SxY4LiBOJ4FCxw3EMezYIHjBuJ4Fixw3EAcz4IFjhuI41mwwHEDcTwLFjhuII5nwQLHDcTxLFjguIE4ngULHDcQx7NggeMG4ngWLHDcQBzPggWOG4jjWbDAcQNxPAsWOG4gjmfBAscNxPEsWOC4gTieBQscNxDHs2CB4wbieBYscNxAHM+C44E/Aa8c86hmtT50AAAAAElFTkSuQmCC'
        })
        saved_map.refresh_from_db()
        self.assertTrue(saved_map.thumbnail)

        # Confirm there is a record of this action
        self.assertEqual(saved_map.activitylog_set.count(), 1)
        self.confirm_activity_log(action, 'data:image/png;base64')

    def test_admin_permission_edit_publicly_visible(self):

        """ Confirm that a logged-in user with the proper permissions
            can edit a publicly visible map
        """

        # Give permission to hide
        permission = Permission.objects.get(name="Can set a map's gallery_visible to hidden")
        test_user = self.test_user
        test_user.user_permissions.add(permission)
        test_user.save()

        client = Client()
        client.login(username='testuser1', password='1X<ISRUkw+tuK')

        # Add a name, thumbnail, and tag, then confirm this map is publicly visible
        saved_map = self.saved_map
        saved_map.gallery_visible = True
        saved_map.name = saved_map.thumbnail = 'test_admin_permission_granted_edit_publicly_visible'
        saved_map.tags.add('real')
        saved_map.save()
        saved_map.refresh_from_db()
        self.assertTrue(saved_map.publicly_visible)

        # We haven't added the permission yet, so the hide action should fail
        response = client.post('/admin/action/', {
            'action': 'hide',
            'map': saved_map.id
        })
        saved_map.refresh_from_db()
        self.assertTrue(saved_map.publicly_visible)

        # Add the permission to edit a publicly visible map
        permission = Permission.objects.get(name="Can edit a publicly visible map")
        test_user = User.objects.get(username='testuser1')
        test_user.user_permissions.add(permission)
        test_user.save()

        # Now the hide action will succeed
        response = client.post('/admin/action/', {
            'action': 'hide',
            'map': saved_map.id
        })
        saved_map.refresh_from_db()
        self.assertFalse(saved_map.publicly_visible)
