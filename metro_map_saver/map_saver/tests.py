import json

from map_saver.models import SavedMap
from map_saver.validator import validate_metro_map

from django.test import TestCase

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


    def test_invalid_toomanylines(self):

        """ Reject a map that has too many lines (Validation #04B: <= 100 lines)
        """
        pass
