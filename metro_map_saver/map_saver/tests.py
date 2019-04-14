import json
from unittest import expectedFailure

from map_saver.models import SavedMap
from map_saver.validator import validate_metro_map

from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.core.exceptions import PermissionDenied

class ValidateMapTestCase(TestCase):

    fixtures = ['backups/2018/mmm-backup-20181110.json']

    def test_fixtures_loaded(self):
        self.assertEqual(SavedMap.objects.count(), 3983)

    def test_validator(self):

        """ Ensure that all maps already saved will pass the validation
              as written in validate_metro_map()
            That way, I'll know any changes to validate_metro_map() have
              at least been tested on a large number of real, existing maps.
        """

        saved_maps = SavedMap.objects.all()
        for saved_map in saved_maps:
            # Ensure that the maps already saved will not be malformed by the validation
            saved_map_data = dict(
                json.loads(
                    str(
                        json.loads(
                            json.dumps(
                                saved_map.mapdata.replace(" u'", "'").replace("{u'", "{'").replace("[u'", "['").replace("'", '"').replace("\\", "").strip('"').strip("'")
                            )
                        )
                    )
                )
            )

            try:
                validated_map = validate_metro_map(
                    str(
                        json.loads(
                            json.dumps(
                                saved_map.mapdata.replace(" u'", "'").replace("{u'", "{'").replace("[u'", "['").replace("'", '"').replace("\\", "").strip('"').strip("'")
                            )
                        )
                    )
                )
            except AssertionError:
                print("Failed validate_metro_map for map #{0}".format(saved_map.id))
                raise

            if saved_map_data != validated_map:
                # Characters like & get converted to &amp; as part of the validation process,
                #   so some maps will not be exactly equal off the bat.

                validated_map = dict(
                    json.loads(
                        json.dumps(
                            validated_map
                        ).replace("&amp;", '&')
                    )
                )

                self.assertEqual(saved_map_data, validated_map,
                    "saved_map.mapdata != validated version for ID: {0}:\n\n{1}\n\n{2}".format(
                        saved_map.id,
                        saved_map_data,
                        validated_map
                    )
                )

    def test_invalid_map_not_dict(self):

        """ Reject a map that is malformed (not a dictionary)
        """
        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 01 metro_map IS NOT DICT: Bad map object, needs to be an object."
        ) as assertion:
            metro_map = '["mapdata", "needs to be a dict"]'
            validate_metro_map(metro_map)

    def test_invalid_map_no_global(self):

        """ Reject a map that has no global key at the root level
        """
        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 02 metro_map DOES NOT HAVE GLOBAL: Bad map object, missing global."
        ) as assertion:
            metro_map = '{"it is a dict": "but has no global"}'
            validate_metro_map(metro_map)

    def test_invalid_map_no_lines(self):

        """ Reject a map that has no rail lines in the global dictionary
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 03 metro_map DOES NOT HAVE LINES: Map does not have any rail lines defined."
        ) as assertion:
            metro_map = '{"global": {"I have global but": "I dont have any lines"} }'
            validate_metro_map(metro_map)

    def test_invalid_map_lines_not_dict(self):

        """ Reject a map that has the global dictionary at the root
            but the lines does not contain a dictionary
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 04 metro_map LINES IS NOT DICT: Map lines must be stored as an object."
        ) as assertion:
            metro_map = '{"global": {"lines": ["this should be a dict, not a list"]} }'
            validate_metro_map(metro_map)

    def test_invalid_toomanylines(self):

        """ Reject a map that has too many lines (Validation #04B: <= 100 lines)
        """

        too_many_lines = {}
        for line in range(101):
            too_many_lines.update(line={"displayName": line})

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 04B metro_map HAS TOO MANY LINES: Map has too many lines (limit is 100); remove unused lines."
        ) as assertion:
            metro_map = '{{"global": {{"lines": {0} }} }}'.format(too_many_lines)
            metro_map = metro_map.replace("'", '"')
            validate_metro_map(metro_map)

    def test_invalid_global_line_not_hex(self):

        """ Reject a map that has a non-hex color in the global lines
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 05 global_line qwerty FAILED is_hex() qwerty is not a valid color: qwerty is not a valid rail line color."
        ) as assertion:
            metro_map = '{"global": {"lines": {"qwerty": {"displayName": "non-hex rail line"} } } }'
            validate_metro_map(metro_map)

    def test_invalid_global_line_wrong_size(self):

        """ Reject a map that has a color in the global lines
                that is not exactly six characters
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 06 global_line beef IS NOT 6 CHARACTERS: The color beef must be 6 characters long."
        ) as assertion:
            metro_map = '{"global": {"lines": {"beef": {"problem": "color code not six chars"} } } }'
            validate_metro_map(metro_map)

    def test_invalid_global_line_display_too_short(self):

        """ Reject a map that has a color in the global lines
                whose display name is zero characters long
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 07 displayName BAD SIZE: Rail line names must be between 1 and 255 characters long (spaces are okay)."
        ):
            metro_map = '{"global" : {"lines": {"000000": {"displayName": ""} } } }'
            validate_metro_map(metro_map)

    def test_invalid_global_line_display_too_long(self):

        """ Reject a map that has a color in the global lines
                whose display name is > 255 characters long
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 07 displayName BAD SIZE: Rail line names must be between 1 and 255 characters long (spaces are okay)."
        ):
            too_long_display_name = "a" * 256
            metro_map = '{{"global" : {{"lines": {{"000000": {{"displayName": "{0}"}} }} }} }}'.format(too_long_display_name)
            validate_metro_map(metro_map)

    def test_invalid_point_line_not_hex(self):

        """ Reject a map that has a non-hex color at a coordinate.
            Coordinates are displayed to the end user 1-indexed.
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 08 nonhex at (1, 1) FAILED is_hex(): Point at (2, 2) is not a valid color: nonhex."
        ) as assertion:
            metro_map = '{"global": { "lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "nonhex"} } }'
            validate_metro_map(metro_map)

    def test_invalid_point_line_not_six(self):

        """ Reject a map that has a color at a coordinate
                that is not six characters long.
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 09 not six characters long at (1, 1) IS NOT 6 CHARACTERS: Point at (2, 2) has a color that needs to be 6 characters long: not six characters long"
        ) as assertion:
            metro_map = '{"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "not six characters long"} } }'
            validate_metro_map(metro_map)

    @expectedFailure
    def test_invalid_point_line_not_valid(self):

        """ Reject a map that has a color at a coordinate
                that is not listed in the global
            (Graceful failure; does not raise an assertion)
        """

        with self.assertNotRaises( # Graceful failure
            AssertionError,
            msg="[VALIDATIONFAILED] 10 ffffff at (1, 1) NOT IN valid_lines: Point at (2, 2) has a color that is not defined in the rail lines; please create a line matching the color ffffff."
        ) as assertion:
            metro_map = '{"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "ffffff"} } }'
            validate_metro_map(metro_map)

    def test_invalid_station_not_dict(self):

        """ Reject a map with a station that is not a dict
        """

        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 11 metro_map[x][y]['station'] at (1, 1) IS NOT DICT: Point at (2, 2) has a malformed station, must be an object."
        ) as assertion:
            metro_map = '{"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": "bad station"} } }'
            validate_metro_map(metro_map)

    def test_invalid_station_name_too_short(self):

        """ Reject a map with a station name that is too short (no characters)
        """
        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 12 station name at (1, 1) BAD SIZE is 0: Point at (2, 2) has a station whose name is not between 1 and 255 characters long. Please rename it."
        ) as assertion:
            metro_map = '{"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": ""} } } }'
            validate_metro_map(metro_map)

    def test_invalid_station_name_too_long(self):

        """ Reject a map with a station name that is too long (> 255 characters)
        """
        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 12 station name at (1, 1) BAD SIZE is 256: Point at (2, 2) has a station whose name is not between 1 and 255 characters long. Please rename it."
        ) as assertion:
            station_name_too_long = "a" * 256
            metro_map = '{{"global": {{"lines": {{"000000": {{"displayName": "Black Line"}} }} }}, "1": {{"1": {{"line": "000000", "station": {{"name": "{0}"}} }} }} }}'.format(station_name_too_long)
            validate_metro_map(metro_map)

    def test_invalid_station_lines_not_list(self):

        """ Reject a map with station lines that are not a list
        """
        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 13 station lines at (1, 1) NOT A LIST: Point at (2, 2) has its station lines in the incorrect format; must be a list."
        ) as assertion:
            metro_map = '{"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": "OK", "lines": "000000"} } } }'
            validate_metro_map(metro_map)

    def test_invalid_station_line_not_hex(self):

        """ Reject a map with a station line that is not hex
        """
        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 15 station_line not hex FAILED is_hex(): Station Rail line not hex is not a valid color."
        ) as assertion:
            metro_map = '{"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": "OK", "lines": ["not hex"]} } } }'
            validate_metro_map(metro_map)

    def test_invalid_station_line_not_six(self):

        """ Reject a map with a station line that is not a color six characters long
        """
        with self.assertRaises(
            AssertionError,
            msg="[VALIDATIONFAILED] 16 station_line beef IS NOT 6 CHARACTERS: Station Rail line color beef needs to be 6 characters long."
        ) as assertion:
            metro_map = '{"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": "OK", "lines": ["beef"]} } } }'
            validate_metro_map(metro_map)

    @expectedFailure
    def test_invalid_station_line_not_valid(self):

        """ Reject a map with a station line that is not in the global
            (Graceful failure; does not raise an assertion)
        """

        with self.assertRaises( # Graceful failure
            AssertionError,
            msg="[VALIDATIONFAILED] 17 station_line ffffff NOT IN valid_lines: Station rail line color ffffff is not defined; please create a rail line matching this color or remove it from all stations."
        ) as assertion:
            metro_map = '{"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": "OK", "lines": ["ffffff"]} } } }'
            validate_metro_map(metro_map)


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
