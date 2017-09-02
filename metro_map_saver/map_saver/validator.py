import json

# metro_map = {"0":{"26":{"line":"a2a2a2"}},"1":{"26":{"line":"a2a2a2"}},"2":{"27":{"line":"a2a2a2"}},"3":{"27":{"line":"a2a2a2"}},"4":{"27":{"line":"a2a2a2"}},"6":{"28":{"line":"a2a2a2"}},"7":{"28":{"line":"a2a2a2"}},"9":{"29":{"line":"a2a2a2"}},"10":{"29":{"line":"a2a2a2"}},"11":{"28":{"line":"a2a2a2"},"29":{"line":"a2a2a2"}},"12":{"28":{"line":"a2a2a2"}},"13":{"24":{"line":"df8600"},"28":{"line":"a2a2a2"}},"14":{"25":{"line":"df8600"},"28":{"line":"a2a2a2"}},"15":{"27":{"line":"a2a2a2"}},"16":{"25":{"line":"df8600"},"27":{"line":"a2a2a2"}},"18":{"27":{"line":"a2a2a2"}},"20":{"26":{"line":"df8600"},"27":{"line":"a2a2a2"}},"21":{"27":{"line":"a2a2a2"}},"22":{"27":{"line":"a2a2a2"}},"23":{"27":{"line":"df8600"}},"24":{"28":{"line":"a2a2a2"}},"25":{"29":{"line":"a2a2a2"}},"27":{"28":{"line":"df8600"},"30":{"line":"a2a2a2"}},"29":{"31":{"line":"a2a2a2"}},"31":{"30":{"line":"df8600"},"32":{"line":"a2a2a2"}},"32":{"32":{"line":"a2a2a2"}},"33":{"32":{"line":"a2a2a2"}},"34":{"31":{"line":"df8600"},"32":{"line":"a2a2a2"},"33":{"line":"a2a2a2"}},"35":{"33":{"line":"a2a2a2"}},"37":{"34":{"line":"a2a2a2"}},"38":{"33":{"line":"df8600"},"35":{"line":"a2a2a2"}},"39":{"10":{"line":"bd1038"},"34":{"line":"df8600"},"44":{"line":"0896d7"},"45":{"line":"0896d7"},"46":{"line":"0896d7"},"47":{"line":"0896d7"},"48":{"line":"0896d7"}},"40":{"36":{"line":"a2a2a2"},"37":{"line":"0896d7"},"38":{"line":"0896d7"},"39":{"line":"0896d7"},"40":{"line":"0896d7"},"41":{"line":"0896d7"},"42":{"line":"0896d7"},"43":{"line":"0896d7"},"44":{"line":"0896d7"}},"41":{"14":{"line":"bd1038"},"35":{"line":"df8600"},"37":{"line":"0896d7"},"38":{"line":"f0ce15"},"39":{"line":"f0ce15"},"40":{"line":"f0ce15"},"41":{"line":"f0ce15"},"42":{"line":"f0ce15"},"43":{"line":"f0ce15"},"44":{"line":"f0ce15","station":{"name":"kjjk","lines":["f0ce15"]}},"45":{"line":"f0ce15"},"46":{"line":"f0ce15"},"47":{"line":"f0ce15"},"48":{"line":"f0ce15"},"49":{"line":"f0ce15"}},"42":{"35":{"line":"df8600"},"36":{"line":"0896d7"},"37":{"line":"0896d7"}},"43":{"20":{"line":"bd1038"},"34":{"line":"f0ce15"},"35":{"line":"f0ce15"},"36":{"line":"0896d7"}},"44":{"31":{"line":"f0ce15"},"32":{"line":"f0ce15"},"33":{"line":"f0ce15"},"34":{"line":"00b251"},"35":{"line":"00b251"},"36":{"line":"00b251"},"37":{"line":"00b251"},"38":{"line":"a2a2a2"}},"45":{"25":{"line":"bd1038"},"30":{"line":"f0ce15"},"31":{"line":"f0ce15"},"33":{"line":"00b251"},"34":{"line":"00b251"},"37":{"line":"0896d7"},"38":{"line":"00b251"},"39":{"line":"00b251"}},"46":{"26":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"33":{"line":"00b251"},"36":{"line":"df8600"},"37":{"line":"0896d7"},"39":{"line":"00b251"},"40":{"line":"a2a2a2"}},"47":{"28":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"0896d7"},"38":{"line":"0896d7"},"40":{"line":"a2a2a2"},"41":{"line":"00b251"}},"48":{"28":{"line":"bd1038","station":{"name":"suilng_","lines":["bd1038","f0ce15","0896d7"]}},"29":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"0896d7"},"41":{"line":"a2a2a2"}},"49":{"28":{"line":"bd1038"},"29":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"0896d7"},"41":{"line":"a2a2a2"}},"50":{"27":{"line":"bd1038"},"28":{"line":"bd1038"},"30":{"line":"f0ce15"},"31":{"line":"00b251"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"df8600"},"39":{"line":"0896d7"},"40":{"line":"a2a2a2"},"42":{"line":"00b251"}},"51":{"25":{"line":"bd1038"},"29":{"line":"f0ce15"},"30":{"line":"00b251"},"31":{"line":"00b251"},"37":{"line":"df8600"},"39":{"line":"a2a2a2"},"42":{"line":"00b251"},"43":{"line":"00b251"}},"52":{"24":{"line":"bd1038"},"28":{"line":"f0ce15"},"29":{"line":"f0ce15"},"30":{"line":"00b251"},"37":{"line":"df8600"},"39":{"line":"0896d7"},"43":{"line":"00b251"},"44":{"line":"00b251"},"45":{"line":"00b251"},"46":{"line":"00b251"}},"53":{"23":{"line":"bd1038"},"24":{"line":"bd1038"},"27":{"line":"f0ce15"},"28":{"line":"f0ce15"},"29":{"line":"00b251","station":{"name":"fyghj","lines":["00b251"]}},"38":{"line":"a2a2a2"},"39":{"line":"0896d7"},"46":{"line":"00b251"}},"54":{"22":{"line":"bd1038"},"23":{"line":"bd1038"},"26":{"line":"f0ce15"},"27":{"line":"f0ce15"},"28":{"line":"00b251"},"29":{"line":"00b251"},"36":{"line":"df8600"},"37":{"line":"df8600"},"38":{"line":"a2a2a2"},"39":{"line":"0896d7"}},"55":{"21":{"line":"bd1038"},"22":{"line":"bd1038"},"25":{"line":"f0ce15"},"26":{"line":"f0ce15"},"27":{"line":"00b251"},"28":{"line":"00b251"},"36":{"line":"df8600"},"39":{"line":"0896d7"},"46":{"line":"00b251"}},"56":{"18":{"line":"bd1038"},"19":{"line":"bd1038"},"20":{"line":"bd1038"},"21":{"line":"bd1038"},"24":{"line":"f0ce15"},"25":{"line":"f0ce15"},"27":{"line":"00b251"},"36":{"line":"a2a2a2"},"39":{"line":"0896d7"},"46":{"line":"00b251"},"47":{"line":"00b251"}},"57":{"13":{"line":"bd1038"},"14":{"line":"bd1038"},"15":{"line":"bd1038"},"16":{"line":"bd1038"},"17":{"line":"bd1038"},"22":{"line":"f0ce15"},"23":{"line":"f0ce15"},"26":{"line":"00b251"},"35":{"line":"df8600"},"39":{"line":"0896d7"},"45":{"line":"00b251"},"46":{"line":"00b251"}},"58":{"8":{"line":"bd1038"},"14":{"line":"bd1038"},"21":{"line":"f0ce15"},"22":{"line":"f0ce15"},"24":{"line":"00b251"},"25":{"line":"00b251"},"35":{"line":"df8600"},"36":{"line":"a2a2a2"},"39":{"line":"0896d7"},"45":{"line":"00b251"}},"59":{"4":{"line":"bd1038"},"5":{"line":"bd1038"},"6":{"line":"bd1038"},"7":{"line":"bd1038"},"8":{"line":"bd1038"},"9":{"line":"bd1038"},"10":{"line":"bd1038"},"11":{"line":"bd1038"},"20":{"line":"f0ce15"},"21":{"line":"f0ce15"},"22":{"line":"00b251"},"23":{"line":"00b251"},"35":{"line":"a2a2a2"},"39":{"line":"0896d7","station":{"name":"79yuhikjn_","lines":["0896d7"]}},"45":{"line":"00b251"}},"60":{"20":{"line":"f0ce15"},"21":{"line":"00b251"},"22":{"line":"00b251"},"34":{"line":"df8600"},"38":{"line":"0896d7"},"44":{"line":"00b251"},"45":{"line":"00b251"}},"61":{"14":{"line":"f0ce15"},"19":{"line":"00b251"},"20":{"line":"00b251"},"35":{"line":"a2a2a2"},"37":{"line":"0896d7"},"43":{"line":"00b251"},"44":{"line":"00b251"}},"62":{"17":{"line":"f0ce15"},"18":{"line":"00b251"},"19":{"line":"00b251"},"34":{"line":"df8600"},"36":{"line":"0896d7"},"37":{"line":"0896d7"},"43":{"line":"00b251"}},"63":{"16":{"line":"f0ce15"},"17":{"line":"00b251"},"18":{"line":"00b251"},"36":{"line":"0896d7"}},"64":{"15":{"line":"f0ce15"},"16":{"line":"00b251"},"17":{"line":"00b251"},"18":{"line":"00b251"},"34":{"line":"df8600"},"35":{"line":"a2a2a2"}},"65":{"14":{"line":"f0ce15"},"15":{"line":"00b251"},"16":{"line":"00b251"},"17":{"line":"00b251"},"33":{"line":"df8600"},"34":{"line":"df8600"},"35":{"line":"0896d7"}},"66":{"12":{"line":"f0ce15"},"13":{"line":"f0ce15"},"14":{"line":"f0ce15"},"15":{"line":"00b251"},"17":{"line":"f0ce15"},"33":{"line":"df8600"},"35":{"line":"a2a2a2"}},"67":{"11":{"line":"f0ce15"},"12":{"line":"f0ce15"},"13":{"line":"f0ce15"},"14":{"line":"00b251"},"17":{"line":"00b251"},"18":{"line":"00b251"},"32":{"line":"df8600"},"35":{"line":"0896d7"}},"68":{"8":{"line":"f0ce15"},"10":{"line":"f0ce15"},"11":{"line":"f0ce15"},"13":{"line":"00b251"},"14":{"line":"00b251"},"31":{"line":"df8600"},"35":{"line":"0896d7"}},"69":{"12":{"line":"00b251"},"13":{"line":"00b251"},"34":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"70":{"30":{"line":"df8600"}},"71":{"29":{"line":"df8600"},"33":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"72":{"32":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"73":{"28":{"line":"df8600"},"32":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"74":{"27":{"line":"df8600"},"32":{"line":"0896d7"}},"75":{"27":{"line":"df8600"},"32":{"line":"0896d7"}},"76":{"26":{"line":"df8600"}},"77":{"26":{"line":"df8600"}},"78":{"25":{"line":"df8600"},"26":{"line":"df8600"}},"global":{"lines":{"bd1038":{"displayName":"Red Line"},"df8600":{"displayName":"Orange Line"},"f0ce15":{"displayName":"Yellow Line"},"00b251":{"displayName":"Green Line"},"0896d7":{"displayName":"Blue Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"}}}}

def is_hex(string):

    """ Determines whether a string is a hexademical string (0-9, a-f) or not
    """

    try:
        int(string, 16)
    except ValueError:
        return False
    else:
        return True

# def hex64(string):

#     """ Given a base16 hexdigest string, shorten it using a base64 variant
#     """

#     # 3 hex: 0-4095
#     # 2 b64: 0-4095

#     # TODO: Implement this so I can shorten URLs too

#     string = string[:12]

#     def b64(hex_three):
#         hex_three = int(hex_three, 16)


#     base64_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'

#     return

def sanitize_string(string):
    return string.replace('<', '').replace('>', '').replace('"', '').replace("'", '&#27;').replace('&', '&amp;').replace('/', '&#x2f;')

def validate_metro_map(metro_map):
    
    """ Validate the MetroMap object by re-constructing it using only valid entries.
    """

    # root-level can only contain keys 0-79 and the key global
    #     0-79 are dict containing only:
    #         "line" with the six-digit hex value of a known line existing in the global
    #         "station" (optional): a dict containing both:
    #             "name": the name of the line, sanitized
    #             "lines": a list containing one or more six-digit hex values of a known line existing in the global
    #             example: {"name":"suilng_","lines":["bd1038","f0ce15","0896d7"]}}
    #     global is a dict containing only:
    #         "lines", a dict with keys of the six-digit hex value of a line
    #                     and the value is another dict:
    #                         displayName: "the display name", sanitized
    #         {"lines":{"bd1038":{"displayName":"Red Line"},"df8600":{"displayName":"Orange Line"},"f0ce15":{"displayName":"Yellow Line"},"00b251":{"displayName":"Green Line"},"0896d7":{"displayName":"Blue Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"}}}}

    validated_metro_map = {}

    assert type(metro_map) == dict
    assert metro_map.get('global')
    assert metro_map['global'].get('lines')
    assert type(metro_map['global']['lines']) == dict

    validated_metro_map = {
        'global': {
            'lines': {

            }
        }
    }

    valid_xy = [str(x) for x in range(80)]
    valid_lines = []

    for global_line in metro_map['global']['lines'].keys():
        assert is_hex(global_line)
        assert len(global_line) == 6
        assert 2 < len(metro_map['global']['lines'][global_line].get('displayName')) < 256
        valid_lines.append(global_line)
        validated_metro_map['global']['lines'][global_line] = {
            'displayName': sanitize_string(metro_map['global']['lines'][global_line]['displayName'])
        }

    for x in metro_map.keys():
        if x == 'global' or x not in valid_xy:
            continue
        if metro_map.get(x):
            if not validated_metro_map.get(x):
                validated_metro_map[x] = {}
            for y in metro_map[x].keys():
                if y not in valid_xy:
                    continue
                if metro_map[x].get(y):
                    if not validated_metro_map[x].get(y):
                        validated_metro_map[x][y] = {}
                    assert is_hex(metro_map[x][y]["line"])
                    assert len(metro_map[x][y]["line"]) == 6
                    assert metro_map[x][y]["line"] in valid_lines
                    validated_metro_map[x][y]["line"] = metro_map[x][y]["line"]
                    if metro_map[x][y].get('station'):
                        assert type(metro_map[x][y]["station"]) == dict
                        assert 2 < len(metro_map[x][y]["station"]["name"])< 256
                        assert type(metro_map[x][y]["station"]["lines"]) == list
                        assert len(metro_map[x][y]["station"]["lines"]) > 0
                        validated_metro_map[x][y]["station"] = {
                            "name": sanitize_string(metro_map[x][y]["station"]["name"].replace('/', '').replace("'", '').replace('&', '')),
                            "lines": []
                        }
                        for station_line in metro_map[x][y]["station"]["lines"]:
                            assert is_hex(station_line)
                            assert len(station_line) == 6
                            assert station_line in valid_lines
                            validated_metro_map[x][y]["station"]["lines"].append(station_line)

    return validated_metro_map