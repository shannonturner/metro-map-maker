import json
from unittest import expectedFailure

from map_saver.forms import CreateMapForm
from map_saver.models import SavedMap
from map_saver.validator import validate_metro_map

from django.test import TestCase, Client
from django.core.exceptions import ObjectDoesNotExist

class PostMapDataMixin:
    def _post_metromap(self, metro_map):

        """ Posts the metro_map to the /save/ endpoint and returns the response as a string
        """

        client = Client()
        response = client.post(
            '/save/',
            {'metroMap': metro_map}
        )

        return response.content.decode('utf-8')

class ValidateMapV2(TestCase):

    """ Test mapDataVersion v2 validation handling
    """

    # Minimum necessary to process this as a v2 map
    v2_minimum = {"global": {"data_version": 2}}

    # To be a VALID map though, it also needs some points
    valid_minimum = {"points_by_color": {"bd1038": {"xys": {"0": {"0": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}

    def test_invalid_maps(self):

        """ Confirm an invalid map will be rejected with a ValidationError.
        """

        invalid_maps = [
            {"json": {}, "expected": "2-01: No points_by_color"},
            {"json": {"points_by_color": []}, "expected": "2-01: No points_by_color"},
            {"json": {"points_by_color": ["truthy"]}, "expected": "2-02: points_by_color must be dict"},
            {"json": {"points_by_color": {"000000": {}}}, "expected": "2-00: This map has no points drawn"},
            {"json": {"points_by_color": {"NOTHEX": {}}}, "expected": "2-03 global line NOTHEX failed is_hex() (Inferred): NOTHEX is not a valid color"},
        ]
        for invalid in invalid_maps:
            invalid['json'].update(self.v2_minimum)
            form = CreateMapForm({'mapdata': invalid['json']})
            self.assertFalse(form.is_valid())
            self.assertIn(invalid['expected'], ';'.join(form.errors['mapdata']))

        # Other invalid maps that have global & shouldn't be clobbered with .update(self.v2_minimum)
        invalid_maps = [
            {"json": {"global": {"data_version": 2, "lines": {"NOTHEX": {}}}, "points_by_color": {"000000": {}}}, "expected": "2-03 global line NOTHEX failed is_hex(): NOTHEX is not a valid color"},
        ]
        for invalid in invalid_maps:
            form = CreateMapForm({'mapdata': invalid['json']})
            self.assertFalse(form.is_valid())
            self.assertIn(invalid['expected'], ';'.join(form.errors['mapdata']))

    def test_infer_line_colors(self):

        """ Confirm that if metro_map['global']['lines'] is false,
                we can still recover by inferring these lines from points_by_color
        """

        maps = [
            # metro_map['global']['lines'] missing entirely
            {"json": {"global": {"data_version": 2}}, "expected": {"bd1038": "bd1038", "00b251": "00b251"},},

            # metro_map['global']['lines'] has a line the other doesn't, we expect all three
            {"json": {"global": {"data_version": 2, "lines": {"0896d7": {"displayName": "Blue Line"}}}}, "expected": {"bd1038": "bd1038", "00b251": "00b251", "0896d7": "Blue Line"},},

            # Can infer line colors from a partial hex
            {"json": {"global": {"data_version": 2, "lines": {"add": {"displayName": "Seafoam"}}}}, "expected": {"aadddd": "Seafoam"},},
            {"json": {"global": {"data_version": 2, "lines": {"a2": {"displayName": "Silver Line"}}}}, "expected": {"a2a2a2": "Silver Line"},},
            {"json": {"global": {"data_version": 2, "lines": {"0": {"displayName": "Black Line"}}}}, "expected": {"000000": "Black Line"},},

            # Truncate if too long
            {"json": {"global": {"data_version": 2, "lines": {"a2" * 100: {"displayName": "Silver Line"}}}}, "expected": {"a2a2a2": "Silver Line"},},

            # Can infer from HTML color name fragments
            {"json": {"global": {"lines": {"reen": {"displayName": "Green"}, "ellow": {"displayName": "Yellow"}, "urple": {"displayName": "Purple"}, "range": {"displayName": "Orange"}, "rey": {"displayName": "Grey"}, "urquoi": {"displayName": "Turquoise"}}}}, "expected": {"008000": "Green", "ffff00": "Yellow", "800080": "Purple", "ffa500": "Orange", "808080": "Grey", "40e0d0": "Turquoise"},},
        ]

        for mmap in maps:
            mmap['json'].update(self.valid_minimum)
            form = CreateMapForm({"mapdata": mmap['json']})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']
            for expectation, line_name in mmap['expected'].items():
                self.assertIn(expectation, mapdata['global']['lines'])
                self.assertEqual(line_name, mapdata['global']['lines'][expectation]['displayName'])

    def test_fix_display_names(self):

        """ Confirm we'll fix invalid displayNames
        """

        maps = [
            # No name -> Rail Line
            {"json": {"global": {"data_version": 2, "lines": {"1": {"displayName": ""}, "2": {"displayName": False}, "3": {"displayName": 0}}}}, "expected": {"111111": "Rail Line", "222222": "Rail Line", "333333": "Rail Line"},},
            {"json": {"global": {"data_version": 2, "lines": {"add": {"displayName": False}}}}, "expected": {"aadddd": "Rail Line"},},
            {"json": {"global": {"data_version": 2, "lines": {"add": {"displayName": 0}}}}, "expected": {"aadddd": "Rail Line"},},

            # Truncated
            {"json": {"global": {"data_version": 2, "lines": {"add": {"displayName": "Seafoam" * 100}}}}, "expected": {"aadddd": ("Seafoam" * 100)[:255]},},
        ]

        for mmap in maps:
            mmap['json'].update(self.valid_minimum)
            form = CreateMapForm({"mapdata": mmap['json']})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']
            for expectation, line_name in mmap['expected'].items():
                self.assertIn(expectation, mapdata['global']['lines'])
                self.assertEqual(line_name, mapdata['global']['lines'][expectation]['displayName'])

    def test_ignore_invalid_points(self):

        """ Confirm we'll ignore and skip invalid points
        """

        # In all these examples, a2a2a2 is bad
        maps = [
            # a2a2a2 missing xys
            {"json": {"points_by_color": {"a2a2a2": {}, "bd1038": {"xys": {"1": {"1": 1}}}}},},

            # xys isn't dict
            {"json": {"points_by_color": {"a2a2a2": {'xys': False}, "bd1038": {"xys": {"1": {"1": 1}}}}},},

            # x isn't dict
            {"json": {"points_by_color": {"a2a2a2": {'xys': {"0": False}}, "bd1038": {"xys": {"1": {"1": 1}}}}},},

            # x isn't int
            {"json": {"points_by_color": {"a2a2a2": {'xys': {"badX": {"1": 1}}}, "bd1038": {"xys": {"1": {"1": 1}}}}},},

            # x is OOB
            {"json": {"points_by_color": {"a2a2a2": {'xys': {"-1": {"1": 1}}}, "bd1038": {"xys": {"1": {"1": 1}}}}},},
            {"json": {"points_by_color": {"a2a2a2": {'xys': {"240": {"1": 1}}}, "bd1038": {"xys": {"1": {"1": 1}}}}},},

            # y isn't int
            {"json": {"points_by_color": {"a2a2a2": {'xys': {"2": {"badY": 1}}}, "bd1038": {"xys": {"1": {"1": 1}}}}},},

            # y is OOB
            {"json": {"points_by_color": {"a2a2a2": {'xys': {"2": {"-2": 1}}}, "bd1038": {"xys": {"1": {"1": 1}}}}},},
            {"json": {"points_by_color": {"a2a2a2": {'xys': {"2": {"240": 1}}}, "bd1038": {"xys": {"1": {"1": 1}}}}},},

            # x,y already seen in a different color
            {"json": {"points_by_color": {"bd1038": {"xys": {"1": {"1": 1}}}, "a2a2a2": {'xys': {"1": {"1": 1}}},}},},
        ]

        for mmap in maps:
            mmap['json'].update(self.v2_minimum)
            form = CreateMapForm({"mapdata": mmap['json']})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']
            self.assertFalse(mapdata['points_by_color'].get('a2a2a2'))

    def test_ignore_invalid_stations(self):

        """ Confirm that we'll ignore and skip invalid stations
        """

        maps = [
            # metro_map['stations'] is false or isn't dict
            {"json": {"stations": False}},
            {"json": {"stations": "not-a-dict"}},

            # metro_map['stations'][x] isn't dict
            {"json": {"stations": {"0": 'not-a-dict'}}},

            # metro_map['stations'][x][y] isn't dict
            {"json": {"stations": {"0": {"0": 'not-a-dict'}}}},

            # x,y isn't on a color
            {"json": {"stations": {"2": {"2": {"name": "Silver Spring"}}}}},
        ]

        for mmap in maps:
            mmap['json'].update(self.v2_minimum)
            mmap['json'].update(self.valid_minimum)
            form = CreateMapForm({"mapdata": mmap['json']})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']
            self.assertFalse(mapdata.get('stations'))

    def test_validate_station(self):

        """ Confirm that station attributes get validated
        """

        maps = [
            # Station gets renamed to be valid
            {"json": {"stations": {"0": {"0": {}}}}, "expected": {"name": "_"}},
            {"json": {"stations": {"0": {"0": {"name": ""}}}}, "expected": {"name": "_"}},
            {"json": {"stations": {"0": {"0": {"name": False}}}}, "expected": {"name": "_"}},
            {"json": {"stations": {"0": {"0": {"name": {}}}}}, "expected": {"name": "_"}},
            {"json": {"stations": {"0": {"0": {"name": "Silver Spring" * 100}}}}, "expected": {"name": ("Silver Spring" * 100)[:255]}},

            # metro_map['stations'][x][y]['orientation'] = 0 if not present or not allowed
            {"json": {"stations": {"0": {"0": {"name": "",}}}}, "expected": {"name": "_", "orientation": 0}},
            {"json": {"stations": {"0": {"0": {"name": "", "orientation": "-999"}}}}, "expected": {"name": "_", "orientation": 0}},

            # metro_map['stations'][x][y]['style'] if present and allowed; blank otherwise
            {"json": {"stations": {"0": {"0": {"style": "invalid"}}}}, "expected": {"name": "_",}, "not expected": {"style": "invalid"}},
            {"json": {"stations": {"0": {"0": {"style": "rect"}}}}, "expected": {"name": "_", "style": "rect"}},

            # metro_map['stations'][x][y]['transfer'] if present: -> = 1
            {"json": {"stations": {"0": {"0": {"transfer": "anything"}}}}, "expected": {"name": "_", "transfer": 1}},
        ]

        for mmap in maps:
            mmap['json'].update(self.v2_minimum)
            mmap['json'].update(self.valid_minimum)
            form = CreateMapForm({"mapdata": mmap['json']})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']
            for k, v in mmap['expected'].items():
                self.assertEqual(v, mapdata['stations']["0"]["0"].get(k))

            for k, v in mmap.get('not expected', {}).items():
                self.assertNotEqual(v, mapdata['stations']["0"]["0"].get(k))

    def test_style_global(self):

        """ Confirm that global styles get validated
        """

        maps = [
            # Neither present
            {'json': {"global": {"data_version": 2}}},

            # Not allowed
            {'json': {"global": {"data_version": 2, "style": {"mapLineWidth": -1, "mapStationStyle": "invalid"}}}},
            {'json': {"global": {"data_version": 2, "style": {"mapLineWidth": "invalid", "mapStationStyle": 1}}}},
        ]

        for mmap in maps:
            mmap['json'].update(self.valid_minimum)
            form = CreateMapForm({"mapdata": mmap['json']})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']
            self.assertEqual(mapdata['global']['style']['mapLineWidth'], 1)
            self.assertEqual(mapdata['global']['style']['mapStationStyle'], 'wmata')

    def test_map_size(self):

        """ Confirm that metro_map['global']['map_size']
            is correct for highest xy seen
        """

        maps = [
            # Basic cases
            {"json": {"points_by_color": {"bd1038": {"xys": {"0": {"0": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 80},
            {"json": {"points_by_color": {"bd1038": {"xys": {"80": {"80": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 120},
            {"json": {"points_by_color": {"bd1038": {"xys": {"120": {"120": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 160},
            {"json": {"points_by_color": {"bd1038": {"xys": {"160": {"160": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 200},
            {"json": {"points_by_color": {"bd1038": {"xys": {"200": {"200": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 240},

            # Single axis
            {"json": {"points_by_color": {"bd1038": {"xys": {"79": {"0": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 80},
            {"json": {"points_by_color": {"bd1038": {"xys": {"0": {"79": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 80},
            {"json": {"points_by_color": {"bd1038": {"xys": {"0": {"100": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 120},
            {"json": {"points_by_color": {"bd1038": {"xys": {"150": {"100": 1}}}, "00b251": {"xys": {"1": {"1": 1}}}}}, "expected": 160},

            # Bad Points
            {"json": {"points_by_color": {"bd1038": {"xys": {"79": {"79": 1}}}, "00b251": {"xys": {"101": {"badY": 1}}}}}, "expected": 80},
            {"json": {"points_by_color": {"bd1038": {"xys": {"110": {"110": 1}}}, "00b251": {"xys": {"201": {"badY": 1}}}}}, "expected": 120},

            # OOB
            {"json": {"points_by_color": {"bd1038": {"xys": {"79": {"79": 1}}}, "00b251": {"xys": {"240": {"1": 1}}}}}, "expected": 80},
        ]

        for mmap in maps:
            mmap['json'].update(self.v2_minimum)
            form = CreateMapForm({"mapdata": mmap['json']})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']
            self.assertEqual(mapdata['global']['map_size'], mmap['expected'])

    def test_valid_v2_map(self):

        """ Confirm various features of a valid v2 map
            get validated and end up unchanged
        """

        maps = [
            {"json": {
                "points_by_color": {
                    "bd1038": {"xys": {
                        "0": {
                            "0": 1,
                            "1": 1,
                            "10": 1,
                        },
                    }},
                    "00b251": {"xys": {
                        "1": {
                            "1": 1,
                            "2": 1,
                            "100": 1,
                            "160": 1,
                        },
                    }},
                },
                "stations": {
                    "0": {
                        "0": {
                            "name": "Silver Spring", "orientation": 45, "style": "circles-sm", "transfer": 1
                        },
                        "1": {
                            "name": "Silver Spring", "orientation": -45, "style": "circles-md",
                        },
                        "10": {
                            "name": "_", "orientation": 180, "style": "circles-lg",
                        },
                    },
                    "1": {
                        "1": {
                            "name": "C", "orientation": 90, "style": "rect-round",
                        },
                        "2": {
                            "name": "D 🚊", "orientation": -90, "style": "rect",
                        },
                        "100": {
                            "name": "E 🚊", "orientation": 135, "style": "wmata",
                        },
                        "160": {
                            "name": "F 🚊", "orientation": -135, "style": "circles-lg",
                        },
                    },
                },
                "global": {
                    "data_version": 2,
                    "map_size": 200,
                    "style": {
                        "mapLineWidth": 0.25,
                        "mapStationStyle": "rect-round",
                    },
                    "lines": {
                        "bd1038": {"displayName": "bd1038"},
                        "00b251": {"displayName": "00b251"},
                    },
                },
            }},
        ]

        for mmap in maps:
            form = CreateMapForm({"mapdata": mmap['json']})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']

            for color in mmap['json']['points_by_color']:
                for x in mmap['json']['points_by_color'][color]['xys']:
                    for y in mmap['json']['points_by_color'][color]['xys'][x]:
                        self.assertEqual(
                            mmap['json']['points_by_color'][color]['xys'][x][y],
                            mapdata['points_by_color'][color]['xys'][x][y],
                        )

            for x in mmap['json']['stations']:
                for y in mmap['json']['stations'][x]:
                    self.assertEqual(
                        mmap['json']['stations'][x][y],
                        mapdata['stations'][x][y],
                    )

            self.assertEqual(
                mmap['json']['global']['style']['mapLineWidth'],
                mapdata['global']['style']['mapLineWidth'],
            )
            self.assertEqual(
                mmap['json']['global']['style']['mapStationStyle'],
                mapdata['global']['style']['mapStationStyle'],
            )
            self.assertEqual(
                mmap['json']['global']['map_size'],
                mapdata['global']['map_size'],
            )
            self.assertEqual(
                mmap['json']['global']['data_version'],
                mapdata['global']['data_version'],
            )

    def test_convert_v1_to_v2(self):

        """ Confirm that we can convert v1 maps to v2 and it's valid
        """

        mmap_v1 = {
            "10": {
                "10": {
                    "line": "008800",
                    "station": {
                        "name": "A", "orientation": -135, "style": "rect", "lines": [],
                    }
                },
                "100": {
                    "line": "008800",
                    "station": {
                        "name": "B", "orientation": -45, "style": "wmata", "lines": [],
                    }
                },
            },
            "global": {
                "lines": {"008800": {"displayName": "Rail Line"},},
                "style": {
                    "mapLineWidth": 0.75,
                    "mapStationStyle": "circles-md",
                },
            },
        }

        form = CreateMapForm({"mapdata": mmap_v1})
        self.assertTrue(form.is_valid())

        # Confirm the cleaned data matches the input
        mapdata_v1 = form.cleaned_data['mapdata']
        self.assertEqual(mapdata_v1["10"]["10"], mmap_v1["10"]["10"])
        self.assertEqual(mapdata_v1["10"]["100"], mmap_v1["10"]["100"])
        self.assertEqual(mapdata_v1["global"]["lines"], mmap_v1["global"]["lines"])
        self.assertEqual(mapdata_v1["global"]["style"], mmap_v1["global"]["style"])

        urlhash_v1 = form.cleaned_data['urlhash']
        saved_map = SavedMap.objects.create(
            urlhash=urlhash_v1,
            mapdata=json.dumps(mapdata_v1),
        )

        # Confirm the saved map (v1) matched the cleaned data
        saved_map = SavedMap.objects.get(urlhash=urlhash_v1)
        saved_map_data = json.loads(saved_map.mapdata)
        self.assertEqual(mapdata_v1["10"]["10"], saved_map_data["10"]["10"])
        self.assertEqual(mapdata_v1["10"]["100"], saved_map_data["10"]["100"])
        self.assertEqual(mapdata_v1["global"], saved_map_data["global"])

        self.assertFalse(saved_map.data)
        saved_map.convert_mapdata_v1_to_v2()
        saved_map.refresh_from_db()

        # Confirm the v2 version of the map has the same points
        self.assertEqual(
            saved_map.data['points_by_color']['008800']['xys']["10"]["10"],
            1,
        )
        self.assertEqual(
            saved_map.data['points_by_color']['008800']['xys']["10"]["100"],
            1,
        )

        # Confirm this has the same stations, too
        self.assertEqual(
            saved_map.data['stations']['10']['10'],
            {"name": "A", "orientation": -135, "style": "rect"},
        )
        self.assertEqual(
            saved_map.data['stations']['10']['100'],
            {"name": "B", "orientation": -45, "style": "wmata"},
        )

        # Global lines & style are the same from v1 to v2
        self.assertEqual(saved_map.data['global']['lines'], saved_map_data['global']['lines'])
        self.assertEqual(saved_map.data['global']['style'], saved_map_data['global']['style'])

        # Data version is new, and we have the map size too
        self.assertEqual(saved_map.data['global']['data_version'], 2)
        self.assertEqual(saved_map.data['global']['map_size'], 120)

        # Re-submit the map; this time it'll validate as v2, giving a new hash
        form = CreateMapForm({"mapdata": saved_map.data})
        self.assertTrue(form.is_valid())
        self.assertNotEqual(urlhash_v1, form.cleaned_data['urlhash'])

        # But the data is the same as before
        self.assertEqual(saved_map.data, form.cleaned_data['mapdata'])

    def test_orientation_string_to_int(self):

        """ Confirm that orientations will be converted from string to int
            during validation
        """

        mapdata = {"global":{"lines":{"00b251":{"displayName":"Green Line"},"0896d7":{"displayName":"Blue Line"},"bd1038":{"displayName":"Red Line"}},"style":{"mapLineWidth":0.125,"mapStationStyle":"circles-thin"},"map_size":80,"data_version":2},"stations":{"1":{"8":{"name":"Green SW","orientation":"45"}},"3":{"3":{"name":"Red NW","style":"rect","transfer":1,"orientation":"-45"}},"7":{"2":{"name":"Blue NE","style":"circles-lg","orientation":"0"}}},"points_by_color":{"00b251":{"xys":{"1":{"7":1,"8":1},"2":{"8":1},"3":{},"4":{},"5":{},"6":{},"7":{},"8":{}}},"0896d7":{"xys":{"2":{},"3":{},"4":{},"5":{},"6":{},"7":{"2":1}}},"bd1038":{"xys":{"3":{"3":1},"4":{},"5":{},"6":{}}}}}
        form = CreateMapForm({"mapdata": mapdata})
        self.assertTrue(form.is_valid())

        self.assertEqual(45, form.cleaned_data['mapdata']['stations']['1']['8']['orientation'])
        self.assertEqual(-45, form.cleaned_data['mapdata']['stations']['3']['3']['orientation'])
        self.assertEqual(0, form.cleaned_data['mapdata']['stations']['7']['2']['orientation'])


class ValidateMap(PostMapDataMixin, TestCase):

    # fixtures = ['backups/2018/mmm-backup-20181110.json']

    # def test_fixtures_loaded(self):
    #     self.assertEqual(SavedMap.objects.count(), 3983)

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

    # def test_invalid_map_not_dict(self):

    #     """ Reject a map that is malformed (not a dictionary)
    #     """
    #     with self.assertRaisesRegex(
    #         AssertionError,
    #         "\[VALIDATIONFAILED\] 01 metro_map IS NOT DICT: Bad map object, needs to be an object."
    #     ) as assertion:
    #         metro_map = ["mapdata", "needs to be a dict"]
    #         validate_metro_map(metro_map)

    #     self.assertIn(
    #         "Bad map object, needs to be an object.",
    #         self._post_metromap(json.dumps(metro_map))
    #     )

    def test_invalid_map_no_global(self):

        """ Reject a map that has no global key at the root level
        """
        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 02 metro_map DOES NOT HAVE GLOBAL: Bad map object, missing global."
        ) as assertion:
            metro_map = {"it is a dict": "but has no global"}
            validate_metro_map(metro_map)

        self.assertIn(
            "Bad map object, missing global.",
            self._post_metromap(json.dumps(metro_map))
        )

    def test_invalid_map_no_lines(self):

        """ Reject a map that has no rail lines in the global dictionary
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 03 metro_map DOES NOT HAVE LINES: Map does not have any rail lines defined."
        ) as assertion:
            metro_map = {"global": {"I have global but": "I dont have any lines"} }
            validate_metro_map(metro_map)

        self.assertIn(
            "Map does not have any rail lines defined.",
            self._post_metromap(json.dumps(metro_map))
        )

    def test_graceful_failure_map_no_lines(self):

        """ Approve a map that has no rail lines in the global dictionary
            but does have these lines in the map data itself
        """

        metro_map = {"40":{"54":{"line":"0896d7","station":{"name":"Tunnford","lines":["0896d7"]}},"55":{"line":"0896d7"},"56":{"line":"0896d7"},"57":{"line":"0896d7"},"58":{"line":"0896d7","station":{"name":"Slarnton","lines":["0896d7"]}},"59":{"line":"0896d7"},"60":{"line":"0896d7"},"61":{"line":"0896d7"},"62":{"line":"0896d7"},"63":{"line":"0896d7"},"64":{"line":"0896d7","station":{"name":"Rondington","lines":["0896d7"]}},"65":{"line":"0896d7"},"66":{"line":"0896d7"},"67":{"line":"0896d7"},"68":{"line":"0896d7"},"69":{"line":"0896d7","station":{"name":"Tardston","lines":["0896d7"]}},"70":{"line":"0896d7"},"71":{"line":"0896d7","station":{"name":"Tardston_Woods","lines":["0896d7"]}}},"global":{"lines":{}}}
        validate_metro_map(metro_map)

        response = self._post_metromap(json.dumps(metro_map))
        urlhash, naming_token = response.split(',')
        self.assertEqual(len(urlhash.strip()), 8)
        self.assertEqual(len(naming_token.strip()), 64)

    def test_invalid_map_lines_not_dict(self):

        """ Reject a map that has the global dictionary at the root
            but the lines does not contain a dictionary
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 04 metro_map LINES IS NOT DICT: Map lines must be stored as an object."
        ) as assertion:
            metro_map = {"global": {"lines": ["this should be a dict, not a list"]} }
            validate_metro_map(metro_map)

        self.assertIn(
            "Map lines must be stored as an object.",
            self._post_metromap(json.dumps(metro_map))
        )

    def test_invalid_toomanylines(self):

        """ Reject a map that has too many lines (Validation #04B: <= 100 lines)
        """

        too_many_lines = {}
        for line in range(101):
            too_many_lines.update(**{str(line): {"displayName": line}})
        self.assertEqual(len(too_many_lines), 101)

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 04B metro_map HAS TOO MANY LINES: Map has too many lines \(limit is 100\); remove unused lines."
        ) as assertion:
            metro_map = '{{"global": {{"lines": {0} }} }}'.format(too_many_lines)
            metro_map = metro_map.replace("'", '"')
            validate_metro_map(json.loads(metro_map))

        self.assertIn(
            "Map has too many lines (limit is 100); remove unused lines.",
            self._post_metromap(metro_map)
        )

    def test_invalid_global_line_not_hex(self):

        """ Reject a map that has a non-hex color in the global lines
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 05 global_line qwerty FAILED is_hex\(\) qwerty is not a valid color: qwerty is not a valid rail line color."
        ) as assertion:
            metro_map = {"global": {"lines": {"qwerty": {"displayName": "non-hex rail line"} } } }
            validate_metro_map(metro_map)

        self.assertIn(
            "qwerty is not a valid rail line color.",
            self._post_metromap(json.dumps(metro_map))
        )

    def test_invalid_global_line_wrong_size(self):

        """ Reject a map that has a color in the global lines
                that is not exactly six characters
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 06 global_line beef IS NOT 6 CHARACTERS: The color beef must be 6 characters long."
        ) as assertion:
            metro_map = {"global": {"lines": {"beef": {"problem": "color code not six chars"} } } }
            validate_metro_map(metro_map)

        self.assertIn(
            "The color beef must be 6 characters long.",
            self._post_metromap(json.dumps(metro_map))
        )

    @expectedFailure
    def test_invalid_global_line_display_too_short(self):

        """ Reject a map that has a color in the global lines
                whose display name is zero characters long
            (Expected failure: gracefully handles by naming 'Rail Line')
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 07 displayName BAD SIZE: Rail line names must be between 1 and 255 characters long \(spaces are okay\)."
        ):
            metro_map = {"global" : {"lines": {"000000": {"displayName": ""} } } }
            validate_metro_map(metro_map)

        self.assertIn(
            "Rail line names must be between 1 and 255 characters long (spaces are okay).",
            self._post_metromap(json.dumps(metro_map))
        )

    @expectedFailure
    def test_invalid_global_line_display_too_long(self):

        """ Reject a map that has a color in the global lines
                whose display name is > 255 characters long

            (Expected failure: gracefully handles by truncation)
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 07 displayName BAD SIZE: Rail line names must be between 1 and 255 characters long \(spaces are okay\)."
        ):
            too_long_display_name = "a" * 256
            metro_map = '{{"global" : {{"lines": {{"000000": {{"displayName": "{0}"}} }} }} }}'.format(too_long_display_name)
            validate_metro_map(json.loads(metro_map))

        self.assertIn(
            "Rail line names must be between 1 and 255 characters long (spaces are okay).",
            self._post_metromap(metro_map)
        )

    def test_global_line_display_removes_backslash_special_chars(self):

        """ Confirm that saving a rail line that somehow had a tab, backspace, or newline in its name will replace that with a space
        """

        metro_map = '{"global": {"lines": {"000000": {"displayName": "Tab\\t\\b\\nCentral"} } } }'
        metro_map = validate_metro_map(json.loads(metro_map))
        self.assertNotIn('\\t', metro_map)
        self.assertNotIn('\\b', metro_map)
        self.assertNotIn('\\n', metro_map)
        self.assertEqual('Tab   Central', metro_map["global"]["lines"]["000000"]["displayName"])

    def test_invalid_point_line_not_hex(self):

        """ Reject a map that has a non-hex color at a coordinate.
            Coordinates are displayed to the end user 1-indexed.
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 08 nonhex at \(1, 1\) FAILED is_hex\(\): Point at \(2, 2\) is not a valid color: nonhex."
        ) as assertion:
            metro_map = {"global": { "lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "nonhex"} } }
            validate_metro_map(metro_map)

        self.assertIn(
            "Point at (2, 2) is not a valid color  nonhex.",
            self._post_metromap(json.dumps(metro_map))
        )

    def test_invalid_point_line_not_six(self):

        """ Reject a map that has a color at a coordinate
                that is not six characters long.
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 09 beef at \(1, 1\) IS NOT 6 CHARACTERS: Point at \(2, 2\) has a color that needs to be 6 characters long: beef"
        ) as assertion:
            metro_map = {"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "beef"} } }
            validate_metro_map(metro_map)

        self.assertIn(
            "Point at (2, 2) has a color that needs to be 6 characters long  beef",
            self._post_metromap(json.dumps(metro_map))
        )

    @expectedFailure
    def test_invalid_point_line_not_valid(self):

        """ Reject a map that has a color at a coordinate
                that is not listed in the global
            (Graceful failure; does not raise an assertion)
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 10 ffffff at \(1, 1\) NOT IN valid_lines: Point at \(2, 2\) has a color that is not defined in the rail lines; please create a line matching the color ffffff."
        ) as assertion:
            metro_map = {"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "ffffff"} } }
            validate_metro_map(metro_map)

    def test_invalid_station_not_dict(self):

        """ Reject a map with a station that is not a dict
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 11 metro_map\[x\]\[y\]\['station'\] at \(1, 1\) IS NOT DICT: Point at \(2, 2\) has a malformed station, must be an object."
        ) as assertion:
            metro_map = {"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": "bad station"} } }
            validate_metro_map(metro_map)

        self.assertIn(
            "Point at (2, 2) has a malformed station, must be an object.",
            self._post_metromap(json.dumps(metro_map))
        )

    @expectedFailure
    def test_invalid_station_name_too_short(self):

        """ Reject a map with a station name that is too short (no characters)
            Now that we are gracefully renaming any station of zero length, we expect this to no longer raise the assertion
        """
        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 12 station name at \(1, 1\) BAD SIZE  is 0: Point at \(2, 2\) has a station whose name is not between 1 and 255 characters long. Please rename it."
        ) as assertion:
            metro_map = {"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": ""} } } }
            validate_metro_map(metro_map)

    def test_invalid_station_name_too_long(self):

        """ Reject a map with a station name that is too long (> 255 characters)
        """
        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 12 station name at \(1, 1\) BAD SIZE a{256} is 256: Point at \(2, 2\) has a station whose name is not between 1 and 255 characters long. Please rename it."
        ) as assertion:
            station_name_too_long = "a" * 256
            metro_map = json.loads('{{"global": {{"lines": {{"000000": {{"displayName": "Black Line"}} }} }}, "1": {{"1": {{"line": "000000", "station": {{"name": "{0}"}} }} }} }}'.format(station_name_too_long))
            validate_metro_map(metro_map)

        self.assertIn(
            "Point at (2, 2) has a station whose name is not between 1 and 255 characters long. Please rename it.",
            self._post_metromap(json.dumps(metro_map))
        )

    def test_invalid_station_lines_not_list(self):

        """ Reject a map with station lines that are not a list
        """
        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 13 station lines at \(1, 1\) NOT A LIST: Point at \(2, 2\) has its station lines in the incorrect format; must be a list."
        ) as assertion:
            metro_map = {"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": "OK", "lines": "000000"} } } }
            validate_metro_map(metro_map)

        self.assertIn(
            "Point at (2, 2) has its station lines in the incorrect format; must be a list.",
            self._post_metromap(json.dumps(metro_map))
        )

    def test_invalid_station_line_not_hex(self):

        """ Reject a map with a station line that is not hex
        """
        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 15 station_line not hex FAILED is_hex\(\): Station Rail line not hex is not a valid color."
        ) as assertion:
            metro_map = {"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": "OK", "lines": ["not hex"]} } } }
            validate_metro_map(metro_map)

        self.assertIn(
            "Station Rail line not hex is not a valid color.",
            self._post_metromap(json.dumps(metro_map))
        )

    def test_invalid_station_line_not_six(self):

        """ Reject a map with a station line that is not a color six characters long
        """
        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 16 station_line beef IS NOT 6 CHARACTERS: Station Rail line color beef needs to be 6 characters long."
        ) as assertion:
            metro_map = {"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": "OK", "lines": ["beef"]} } } }
            validate_metro_map(metro_map)

        self.assertIn(
            "Station Rail line color beef needs to be 6 characters long.",
            self._post_metromap(json.dumps(metro_map))
        )

    @expectedFailure
    def test_invalid_station_line_not_valid(self):

        """ Reject a map with a station line that is not in the global
            (Graceful failure; does not raise an assertion)
        """

        with self.assertRaisesRegex(
            AssertionError,
            "\[VALIDATIONFAILED\] 17 station_line ffffff NOT IN valid_lines: Station rail line color ffffff is not defined; please create a rail line matching this color or remove it from all stations."
        ) as assertion:
            metro_map = {"global": {"lines": {"000000": {"displayName": "Black Line"} } }, "1": {"1": {"line": "000000", "station": {"name": "OK", "lines": ["ffffff"]} } } }
            validate_metro_map(metro_map)

    def test_valid_map_saves(self):

        """ Confirm that a posting a valid map will save it
        """

        # First, confirm that we do not have this map yet
        with self.assertRaises(ObjectDoesNotExist):
            SavedMap.objects.get(urlhash='I0F8Rza4')

        map_data = json.dumps({"8":{"8":{"line":"bd1038"}},"global":{"lines":{"0896d7":{"displayName":"Blue Line"},"df8600":{"displayName":"Orange Line"},"000000":{"displayName":"Logo"},"00b251":{"displayName":"Green Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"},"f0ce15":{"displayName":"Yellow Line"},"bd1038":{"displayName":"Red Line"},"79bde9":{"displayName":"Rivers"},"cfe4a7":{"displayName":"Parks"}}}})

        client = Client()
        client.post('/save/', {
            'metroMap': map_data
        })

        saved_map = SavedMap.objects.get(urlhash='I0F8Rza4')
        self.assertTrue(saved_map)

        # Confirm that multiple posts with the same data return the same urlhash
        response = client.post('/save/', {
            'metroMap': map_data
        })

        self.assertEqual(
            b'I0F8Rza4',
            response.content.strip().split(b',')[0]
        )

        # Confirm that the mapdata and urlhash are both identical to the original
        # ... well, close to identical, anyway. validation adds some extra info:
        map_data = json.loads(map_data)
        map_data['global']["style"] = {"mapLineWidth": 1, "mapStationStyle": "wmata"}
        map_data['global']["data_version"] = 1
        saved_map.refresh_from_db()
        self.assertDictEqual(
            json.loads(saved_map.mapdata),
            map_data,
        )
        self.assertEqual(
            saved_map.urlhash,
            'I0F8Rza4'
        )

    def test_valid_map_name(self):

        """ Confirm that a post containing the proper naming token will allow you to name a map
        """

        saved_map = SavedMap.objects.create(**{
            'urlhash': 'test_valid_map_name'[:8],
            'naming_token': 'abcdef123',
            'name': '',
            'mapdata': ''
        })

        self.assertEqual('', saved_map.name)

        client = Client()
        client.post('/name/', {
            'urlhash': 'test_valid_map_name'[:8],
            'naming_token': 'abcdef123',
            'name': 'hooray',
            'tags': 'coolmap'
        })

        saved_map.refresh_from_db()

        # Tags from users are not directly applied;
        #   they are appended to the name
        self.assertEqual('hooray (coolmap)', saved_map.name)

    def test_invalid_naming_token(self):

        """ Confirm that a post containing a blank or invalid naming token will not overwrite a map's name
        """

        saved_map = SavedMap.objects.create(**{
            'urlhash': 'test_invalid_naming_token'[:8],
            'naming_token': '',
            'name': 'set in stone',
            'mapdata': ''
        })
        self.assertEqual('set in stone', saved_map.name)

        # Confirm a blank naming token doesn't match a blank naming token
        client = Client()
        client.post('/name/', {
            'urlhash': 'test_invalid_naming_token'[:8],
            'naming_token': '',
            'name': 'hooray',
            'tags': 'coolmap'
        })
        saved_map.refresh_from_db()
        self.assertEqual('set in stone', saved_map.name)

        # Confirm that a naming token doesn't work with a blank naming token
        client.post('/name/', {
            'urlhash': 'test_invalid_naming_token'[:8],
            'naming_token': 'wrong naming token',
            'name': 'hooray',
            'tags': 'coolmap'
        })
        saved_map.refresh_from_db()
        self.assertEqual('set in stone', saved_map.name)

        # Set the map's naming token
        saved_map.naming_token = 'token'
        saved_map.save()

        # Confirm the incorrect naming token doesn't work either
        client.post('/name/', {
            'urlhash': 'test_invalid_naming_token'[:8],
            'naming_token': 'wrong naming token',
            'name': 'hooray',
            'tags': 'coolmap'
        })
        saved_map.refresh_from_db()
        self.assertEqual('set in stone', saved_map.name)

    def test_valid_map_station_lines(self):

        """ Confirm that I'm safe to remove the
            "Rail Lines this Station serves" feature
            without causing any maps to fail validation.

            Valid maps include:
            No ["station"]["lines"] at all
            ["station"]["lines"] is an empty list
            ["station"]["lines"] is a list of hex values I don't have in the globals
        """

        metro_map = {"8":{"8":{"line":"bd1038","station":{"name":"Nice Station"}}},"global":{"lines":{"0896d7":{"displayName":"Blue Line"},"df8600":{"displayName":"Orange Line"},"000000":{"displayName":"Logo"},"00b251":{"displayName":"Green Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"},"f0ce15":{"displayName":"Yellow Line"},"bd1038":{"displayName":"Red Line"},"79bde9":{"displayName":"Rivers"},"cfe4a7":{"displayName":"Parks"}}}}
        validate_metro_map(metro_map)
        response = self._post_metromap(json.dumps(metro_map)).strip()
        # 73 = 8 character urlhash + comma + 64 char naming token
        self.assertTrue(len(response), 73)

        metro_map = {"8":{"8":{"line":"bd1038","station":{"name":"Nice Station", "lines": []}}},"global":{"lines":{"0896d7":{"displayName":"Blue Line"},"df8600":{"displayName":"Orange Line"},"000000":{"displayName":"Logo"},"00b251":{"displayName":"Green Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"},"f0ce15":{"displayName":"Yellow Line"},"bd1038":{"displayName":"Red Line"},"79bde9":{"displayName":"Rivers"},"cfe4a7":{"displayName":"Parks"}}}}
        validate_metro_map(metro_map)
        response = self._post_metromap(json.dumps(metro_map)).strip()
        self.assertTrue(len(response), 73)

        metro_map = {"8":{"8":{"line":"bd1038","station":{"name":"Nice Station", "lines": ['123456', '678909']}}},"global":{"lines":{"0896d7":{"displayName":"Blue Line"},"df8600":{"displayName":"Orange Line"},"000000":{"displayName":"Logo"},"00b251":{"displayName":"Green Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"},"f0ce15":{"displayName":"Yellow Line"},"bd1038":{"displayName":"Red Line"},"79bde9":{"displayName":"Rivers"},"cfe4a7":{"displayName":"Parks"}}}}
        validate_metro_map(metro_map)
        response = self._post_metromap(json.dumps(metro_map)).strip()
        self.assertTrue(len(response), 73)

    def test_valid_map_html_color_name_fragments(self):

        """ Confirm that an otherwise-valid map
            that uses HTML color names in the globals instead of hex values
            will still be accepted
        """

        # Truncated from an assortment of actual failed maps from the logs
        metro_maps = [
            {"50":{},"51":{"190":{"line":"008800","station":{"name":"Cloverdale","orientation":"180","lines":["reen"]}}},"global":{"lines":{"002366":{"displayName":"Line 3 Ontario"},"f81894":{"displayName":"Line 7 Jane"},"reen":{"displayName":"Line 2 Bloor-Danforth"},"ellow":{"displayName":"Line 1 Yonge-University"},"urple":{"displayName":"Line 4 Sheppard"},"range":{"displayName":"Line 5 Eglinton"},"rey":{"displayName":"Line 6 Finch West"},"urquoi":{"displayName":"Line 8 Don Mills"}}}},
        ]

        for metro_map in metro_maps:
            validate_metro_map(metro_map)
            response = self._post_metromap(json.dumps(metro_map)).strip()
            # 73 = 8 character urlhash + comma + 64 char naming token
            self.assertTrue(len(response), 73)

    def test_valid_map_v1_allows_styles(self):

        """ Confirm that styles can be backported to v1
        """

        metro_maps = [
            {
                "10": {
                    "10": {
                        "line": "008800",
                        "station": {
                            "name": "A", "orientation": 180, "style": "rect-round", "lines": [],
                        }
                    }
                },
                "global": {
                    "lines": {"008800": {"displayName": "test_valid_map_v1_allows_styles"},},
                    "style": {
                        "mapLineWidth": 0.5,
                        "mapStationStyle": "circles-sm",
                    },
                },
            },
        ]

        for metro_map in metro_maps:
            form = CreateMapForm({"mapdata": metro_map})
            self.assertTrue(form.is_valid())

            mapdata = form.cleaned_data['mapdata']
            for x in metro_map:
                if not x.isdigit():
                    continue
                for y in metro_map[x]:
                    self.assertEqual(mapdata[x][y], metro_map[x][y])

            self.assertEqual(
                mapdata['global']['style'],
                metro_map['global']['style'],
            )

    def test_orientation_string_to_int(self):

        """ Confirm that string orientations will be converted to ints
        """

        mapdata = {"1":{"8":{"line":"00b251","station":{"name":"Green SW","lines":[],"orientation":"45"}}},"2":{"8":{"line":"00b251"}},"3":{"3":{"line":"bd1038","station":{"name":"Red NW","lines":[],"orientation":"-45"}}},"7":{"2":{"line":"0896d7","station":{"name":"Blue E","lines":[],"orientation":"0"}}},"global":{"lines":{"00b251":{"displayName":"Green Line"},"0896d7":{"displayName":"Blue Line"},"bd1038":{"displayName":"Red Line"}},"style":{"mapLineWidth":0.125,"mapStationStyle":"circles-thin"},"data_version":1,"map_size":80}}
        form = CreateMapForm({"mapdata": mapdata})
        self.assertTrue(form.is_valid())

        self.assertEqual(45, form.cleaned_data['mapdata']['1']['8']['station']['orientation'])
        self.assertEqual(-45, form.cleaned_data['mapdata']['3']['3']['station']['orientation'])
        self.assertEqual(0, form.cleaned_data['mapdata']['7']['2']['station']['orientation'])
