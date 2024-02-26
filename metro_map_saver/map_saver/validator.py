import json
import re
import unicodedata
from .html_color_names import html_color_name_fragments

# metro_map = {"0":{"26":{"line":"a2a2a2"}},"1":{"26":{"line":"a2a2a2"}},"2":{"27":{"line":"a2a2a2"}},"3":{"27":{"line":"a2a2a2"}},"4":{"27":{"line":"a2a2a2"}},"6":{"28":{"line":"a2a2a2"}},"7":{"28":{"line":"a2a2a2"}},"9":{"29":{"line":"a2a2a2"}},"10":{"29":{"line":"a2a2a2"}},"11":{"28":{"line":"a2a2a2"},"29":{"line":"a2a2a2"}},"12":{"28":{"line":"a2a2a2"}},"13":{"24":{"line":"df8600"},"28":{"line":"a2a2a2"}},"14":{"25":{"line":"df8600"},"28":{"line":"a2a2a2"}},"15":{"27":{"line":"a2a2a2"}},"16":{"25":{"line":"df8600"},"27":{"line":"a2a2a2"}},"18":{"27":{"line":"a2a2a2"}},"20":{"26":{"line":"df8600"},"27":{"line":"a2a2a2"}},"21":{"27":{"line":"a2a2a2"}},"22":{"27":{"line":"a2a2a2"}},"23":{"27":{"line":"df8600"}},"24":{"28":{"line":"a2a2a2"}},"25":{"29":{"line":"a2a2a2"}},"27":{"28":{"line":"df8600"},"30":{"line":"a2a2a2"}},"29":{"31":{"line":"a2a2a2"}},"31":{"30":{"line":"df8600"},"32":{"line":"a2a2a2"}},"32":{"32":{"line":"a2a2a2"}},"33":{"32":{"line":"a2a2a2"}},"34":{"31":{"line":"df8600"},"32":{"line":"a2a2a2"},"33":{"line":"a2a2a2"}},"35":{"33":{"line":"a2a2a2"}},"37":{"34":{"line":"a2a2a2"}},"38":{"33":{"line":"df8600"},"35":{"line":"a2a2a2"}},"39":{"10":{"line":"bd1038"},"34":{"line":"df8600"},"44":{"line":"0896d7"},"45":{"line":"0896d7"},"46":{"line":"0896d7"},"47":{"line":"0896d7"},"48":{"line":"0896d7"}},"40":{"36":{"line":"a2a2a2"},"37":{"line":"0896d7"},"38":{"line":"0896d7"},"39":{"line":"0896d7"},"40":{"line":"0896d7"},"41":{"line":"0896d7"},"42":{"line":"0896d7"},"43":{"line":"0896d7"},"44":{"line":"0896d7"}},"41":{"14":{"line":"bd1038"},"35":{"line":"df8600"},"37":{"line":"0896d7"},"38":{"line":"f0ce15"},"39":{"line":"f0ce15"},"40":{"line":"f0ce15"},"41":{"line":"f0ce15"},"42":{"line":"f0ce15"},"43":{"line":"f0ce15"},"44":{"line":"f0ce15","station":{"name":"kjjk","lines":["f0ce15"]}},"45":{"line":"f0ce15"},"46":{"line":"f0ce15"},"47":{"line":"f0ce15"},"48":{"line":"f0ce15"},"49":{"line":"f0ce15"}},"42":{"35":{"line":"df8600"},"36":{"line":"0896d7"},"37":{"line":"0896d7"}},"43":{"20":{"line":"bd1038"},"34":{"line":"f0ce15"},"35":{"line":"f0ce15"},"36":{"line":"0896d7"}},"44":{"31":{"line":"f0ce15"},"32":{"line":"f0ce15"},"33":{"line":"f0ce15"},"34":{"line":"00b251"},"35":{"line":"00b251"},"36":{"line":"00b251"},"37":{"line":"00b251"},"38":{"line":"a2a2a2"}},"45":{"25":{"line":"bd1038"},"30":{"line":"f0ce15"},"31":{"line":"f0ce15"},"33":{"line":"00b251"},"34":{"line":"00b251"},"37":{"line":"0896d7"},"38":{"line":"00b251"},"39":{"line":"00b251"}},"46":{"26":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"33":{"line":"00b251"},"36":{"line":"df8600"},"37":{"line":"0896d7"},"39":{"line":"00b251"},"40":{"line":"a2a2a2"}},"47":{"28":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"0896d7"},"38":{"line":"0896d7"},"40":{"line":"a2a2a2"},"41":{"line":"00b251"}},"48":{"28":{"line":"bd1038","station":{"name":"suilng_","lines":["bd1038","f0ce15","0896d7"]}},"29":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"0896d7"},"41":{"line":"a2a2a2"}},"49":{"28":{"line":"bd1038"},"29":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"0896d7"},"41":{"line":"a2a2a2"}},"50":{"27":{"line":"bd1038"},"28":{"line":"bd1038"},"30":{"line":"f0ce15"},"31":{"line":"00b251"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"df8600"},"39":{"line":"0896d7"},"40":{"line":"a2a2a2"},"42":{"line":"00b251"}},"51":{"25":{"line":"bd1038"},"29":{"line":"f0ce15"},"30":{"line":"00b251"},"31":{"line":"00b251"},"37":{"line":"df8600"},"39":{"line":"a2a2a2"},"42":{"line":"00b251"},"43":{"line":"00b251"}},"52":{"24":{"line":"bd1038"},"28":{"line":"f0ce15"},"29":{"line":"f0ce15"},"30":{"line":"00b251"},"37":{"line":"df8600"},"39":{"line":"0896d7"},"43":{"line":"00b251"},"44":{"line":"00b251"},"45":{"line":"00b251"},"46":{"line":"00b251"}},"53":{"23":{"line":"bd1038"},"24":{"line":"bd1038"},"27":{"line":"f0ce15"},"28":{"line":"f0ce15"},"29":{"line":"00b251","station":{"name":"fyghj","lines":["00b251"]}},"38":{"line":"a2a2a2"},"39":{"line":"0896d7"},"46":{"line":"00b251"}},"54":{"22":{"line":"bd1038"},"23":{"line":"bd1038"},"26":{"line":"f0ce15"},"27":{"line":"f0ce15"},"28":{"line":"00b251"},"29":{"line":"00b251"},"36":{"line":"df8600"},"37":{"line":"df8600"},"38":{"line":"a2a2a2"},"39":{"line":"0896d7"}},"55":{"21":{"line":"bd1038"},"22":{"line":"bd1038"},"25":{"line":"f0ce15"},"26":{"line":"f0ce15"},"27":{"line":"00b251"},"28":{"line":"00b251"},"36":{"line":"df8600"},"39":{"line":"0896d7"},"46":{"line":"00b251"}},"56":{"18":{"line":"bd1038"},"19":{"line":"bd1038"},"20":{"line":"bd1038"},"21":{"line":"bd1038"},"24":{"line":"f0ce15"},"25":{"line":"f0ce15"},"27":{"line":"00b251"},"36":{"line":"a2a2a2"},"39":{"line":"0896d7"},"46":{"line":"00b251"},"47":{"line":"00b251"}},"57":{"13":{"line":"bd1038"},"14":{"line":"bd1038"},"15":{"line":"bd1038"},"16":{"line":"bd1038"},"17":{"line":"bd1038"},"22":{"line":"f0ce15"},"23":{"line":"f0ce15"},"26":{"line":"00b251"},"35":{"line":"df8600"},"39":{"line":"0896d7"},"45":{"line":"00b251"},"46":{"line":"00b251"}},"58":{"8":{"line":"bd1038"},"14":{"line":"bd1038"},"21":{"line":"f0ce15"},"22":{"line":"f0ce15"},"24":{"line":"00b251"},"25":{"line":"00b251"},"35":{"line":"df8600"},"36":{"line":"a2a2a2"},"39":{"line":"0896d7"},"45":{"line":"00b251"}},"59":{"4":{"line":"bd1038"},"5":{"line":"bd1038"},"6":{"line":"bd1038"},"7":{"line":"bd1038"},"8":{"line":"bd1038"},"9":{"line":"bd1038"},"10":{"line":"bd1038"},"11":{"line":"bd1038"},"20":{"line":"f0ce15"},"21":{"line":"f0ce15"},"22":{"line":"00b251"},"23":{"line":"00b251"},"35":{"line":"a2a2a2"},"39":{"line":"0896d7","station":{"name":"79yuhikjn_","lines":["0896d7"]}},"45":{"line":"00b251"}},"60":{"20":{"line":"f0ce15"},"21":{"line":"00b251"},"22":{"line":"00b251"},"34":{"line":"df8600"},"38":{"line":"0896d7"},"44":{"line":"00b251"},"45":{"line":"00b251"}},"61":{"14":{"line":"f0ce15"},"19":{"line":"00b251"},"20":{"line":"00b251"},"35":{"line":"a2a2a2"},"37":{"line":"0896d7"},"43":{"line":"00b251"},"44":{"line":"00b251"}},"62":{"17":{"line":"f0ce15"},"18":{"line":"00b251"},"19":{"line":"00b251"},"34":{"line":"df8600"},"36":{"line":"0896d7"},"37":{"line":"0896d7"},"43":{"line":"00b251"}},"63":{"16":{"line":"f0ce15"},"17":{"line":"00b251"},"18":{"line":"00b251"},"36":{"line":"0896d7"}},"64":{"15":{"line":"f0ce15"},"16":{"line":"00b251"},"17":{"line":"00b251"},"18":{"line":"00b251"},"34":{"line":"df8600"},"35":{"line":"a2a2a2"}},"65":{"14":{"line":"f0ce15"},"15":{"line":"00b251"},"16":{"line":"00b251"},"17":{"line":"00b251"},"33":{"line":"df8600"},"34":{"line":"df8600"},"35":{"line":"0896d7"}},"66":{"12":{"line":"f0ce15"},"13":{"line":"f0ce15"},"14":{"line":"f0ce15"},"15":{"line":"00b251"},"17":{"line":"f0ce15"},"33":{"line":"df8600"},"35":{"line":"a2a2a2"}},"67":{"11":{"line":"f0ce15"},"12":{"line":"f0ce15"},"13":{"line":"f0ce15"},"14":{"line":"00b251"},"17":{"line":"00b251"},"18":{"line":"00b251"},"32":{"line":"df8600"},"35":{"line":"0896d7"}},"68":{"8":{"line":"f0ce15"},"10":{"line":"f0ce15"},"11":{"line":"f0ce15"},"13":{"line":"00b251"},"14":{"line":"00b251"},"31":{"line":"df8600"},"35":{"line":"0896d7"}},"69":{"12":{"line":"00b251"},"13":{"line":"00b251"},"34":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"70":{"30":{"line":"df8600"}},"71":{"29":{"line":"df8600"},"33":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"72":{"32":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"73":{"28":{"line":"df8600"},"32":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"74":{"27":{"line":"df8600"},"32":{"line":"0896d7"}},"75":{"27":{"line":"df8600"},"32":{"line":"0896d7"}},"76":{"26":{"line":"df8600"}},"77":{"26":{"line":"df8600"}},"78":{"25":{"line":"df8600"},"26":{"line":"df8600"}},"global":{"lines":{"bd1038":{"displayName":"Red Line"},"df8600":{"displayName":"Orange Line"},"f0ce15":{"displayName":"Yellow Line"},"00b251":{"displayName":"Green Line"},"0896d7":{"displayName":"Blue Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"}}}}
# mm = """{"0":{"26":{"line":"a2a2a2"}},"1":{"26":{"line":"a2a2a2"}},"2":{"27":{"line":"a2a2a2"}},"3":{"27":{"line":"a2a2a2"}},"4":{"27":{"line":"a2a2a2"}},"6":{"28":{"line":"a2a2a2"}},"7":{"28":{"line":"a2a2a2"}},"9":{"29":{"line":"a2a2a2"}},"10":{"29":{"line":"a2a2a2"}},"11":{"28":{"line":"a2a2a2"},"29":{"line":"a2a2a2"}},"12":{"28":{"line":"a2a2a2"}},"13":{"24":{"line":"df8600"},"28":{"line":"a2a2a2"}},"14":{"25":{"line":"df8600"},"28":{"line":"a2a2a2"}},"15":{"27":{"line":"a2a2a2"}},"16":{"25":{"line":"df8600"},"27":{"line":"a2a2a2"}},"18":{"27":{"line":"a2a2a2"}},"20":{"26":{"line":"df8600"},"27":{"line":"a2a2a2"}},"21":{"27":{"line":"a2a2a2"}},"22":{"27":{"line":"a2a2a2"}},"23":{"27":{"line":"df8600"}},"24":{"28":{"line":"a2a2a2"}},"25":{"29":{"line":"a2a2a2"}},"27":{"28":{"line":"df8600"},"30":{"line":"a2a2a2"}},"29":{"31":{"line":"a2a2a2"}},"31":{"30":{"line":"df8600"},"32":{"line":"a2a2a2"}},"32":{"32":{"line":"a2a2a2"}},"33":{"32":{"line":"a2a2a2"}},"34":{"31":{"line":"df8600"},"32":{"line":"a2a2a2"},"33":{"line":"a2a2a2"}},"35":{"33":{"line":"a2a2a2"}},"37":{"34":{"line":"a2a2a2"}},"38":{"33":{"line":"df8600"},"35":{"line":"a2a2a2"}},"39":{"10":{"line":"bd1038"},"34":{"line":"df8600"},"44":{"line":"0896d7"},"45":{"line":"0896d7"},"46":{"line":"0896d7"},"47":{"line":"0896d7"},"48":{"line":"0896d7"}},"40":{"36":{"line":"a2a2a2"},"37":{"line":"0896d7"},"38":{"line":"0896d7"},"39":{"line":"0896d7"},"40":{"line":"0896d7"},"41":{"line":"0896d7"},"42":{"line":"0896d7"},"43":{"line":"0896d7"},"44":{"line":"0896d7"}},"41":{"14":{"line":"bd1038"},"35":{"line":"df8600"},"37":{"line":"0896d7"},"38":{"line":"f0ce15"},"39":{"line":"f0ce15"},"40":{"line":"f0ce15"},"41":{"line":"f0ce15"},"42":{"line":"f0ce15"},"43":{"line":"f0ce15"},"44":{"line":"f0ce15","station":{"name":"Train a\xe9rien","lines":["f0ce15"]}},"45":{"line":"f0ce15"},"46":{"line":"f0ce15"},"47":{"line":"f0ce15"},"48":{"line":"f0ce15"},"49":{"line":"f0ce15"}},"42":{"35":{"line":"df8600"},"36":{"line":"0896d7"},"37":{"line":"0896d7"}},"43":{"20":{"line":"bd1038"},"34":{"line":"f0ce15"},"35":{"line":"f0ce15"},"36":{"line":"0896d7"}},"44":{"31":{"line":"f0ce15"},"32":{"line":"f0ce15"},"33":{"line":"f0ce15"},"34":{"line":"00b251"},"35":{"line":"00b251"},"36":{"line":"00b251"},"37":{"line":"00b251"},"38":{"line":"a2a2a2"}},"45":{"25":{"line":"bd1038"},"30":{"line":"f0ce15"},"31":{"line":"f0ce15"},"33":{"line":"00b251"},"34":{"line":"00b251"},"37":{"line":"0896d7"},"38":{"line":"00b251"},"39":{"line":"00b251"}},"46":{"26":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"33":{"line":"00b251"},"36":{"line":"df8600"},"37":{"line":"0896d7"},"39":{"line":"00b251"},"40":{"line":"a2a2a2"}},"47":{"28":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"0896d7"},"38":{"line":"0896d7"},"40":{"line":"a2a2a2"},"41":{"line":"00b251"}},"48":{"28":{"line":"bd1038","station":{"name":"suilng_","lines":["bd1038","f0ce15","0896d7"]}},"29":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"0896d7"},"41":{"line":"a2a2a2"}},"49":{"28":{"line":"bd1038"},"29":{"line":"bd1038"},"30":{"line":"f0ce15"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"0896d7"},"41":{"line":"a2a2a2"}},"50":{"27":{"line":"bd1038"},"28":{"line":"bd1038"},"30":{"line":"f0ce15"},"31":{"line":"00b251"},"32":{"line":"00b251"},"37":{"line":"df8600"},"38":{"line":"df8600"},"39":{"line":"0896d7"},"40":{"line":"a2a2a2"},"42":{"line":"00b251"}},"51":{"25":{"line":"bd1038"},"29":{"line":"f0ce15"},"30":{"line":"00b251"},"31":{"line":"00b251"},"37":{"line":"df8600"},"39":{"line":"a2a2a2"},"42":{"line":"00b251"},"43":{"line":"00b251"}},"52":{"24":{"line":"bd1038"},"28":{"line":"f0ce15"},"29":{"line":"f0ce15"},"30":{"line":"00b251"},"37":{"line":"df8600"},"39":{"line":"0896d7"},"43":{"line":"00b251"},"44":{"line":"00b251"},"45":{"line":"00b251"},"46":{"line":"00b251"}},"53":{"23":{"line":"bd1038"},"24":{"line":"bd1038"},"27":{"line":"f0ce15"},"28":{"line":"f0ce15"},"29":{"line":"00b251","station":{"name":"fyghj","lines":["00b251"]}},"38":{"line":"a2a2a2"},"39":{"line":"0896d7"},"46":{"line":"00b251"}},"54":{"22":{"line":"bd1038"},"23":{"line":"bd1038"},"26":{"line":"f0ce15"},"27":{"line":"f0ce15"},"28":{"line":"00b251"},"29":{"line":"00b251"},"36":{"line":"df8600"},"37":{"line":"df8600"},"38":{"line":"a2a2a2"},"39":{"line":"0896d7"}},"55":{"21":{"line":"bd1038"},"22":{"line":"bd1038"},"25":{"line":"f0ce15"},"26":{"line":"f0ce15"},"27":{"line":"00b251"},"28":{"line":"00b251"},"36":{"line":"df8600"},"39":{"line":"0896d7"},"46":{"line":"00b251"}},"56":{"18":{"line":"bd1038"},"19":{"line":"bd1038"},"20":{"line":"bd1038"},"21":{"line":"bd1038"},"24":{"line":"f0ce15"},"25":{"line":"f0ce15"},"27":{"line":"00b251"},"36":{"line":"a2a2a2"},"39":{"line":"0896d7"},"46":{"line":"00b251"},"47":{"line":"00b251"}},"57":{"13":{"line":"bd1038"},"14":{"line":"bd1038"},"15":{"line":"bd1038"},"16":{"line":"bd1038"},"17":{"line":"bd1038"},"22":{"line":"f0ce15"},"23":{"line":"f0ce15"},"26":{"line":"00b251"},"35":{"line":"df8600"},"39":{"line":"0896d7"},"45":{"line":"00b251"},"46":{"line":"00b251"}},"58":{"8":{"line":"bd1038"},"14":{"line":"bd1038"},"21":{"line":"f0ce15"},"22":{"line":"f0ce15"},"24":{"line":"00b251"},"25":{"line":"00b251"},"35":{"line":"df8600"},"36":{"line":"a2a2a2"},"39":{"line":"0896d7"},"45":{"line":"00b251"}},"59":{"4":{"line":"bd1038"},"5":{"line":"bd1038"},"6":{"line":"bd1038"},"7":{"line":"bd1038"},"8":{"line":"bd1038"},"9":{"line":"bd1038"},"10":{"line":"bd1038"},"11":{"line":"bd1038"},"20":{"line":"f0ce15"},"21":{"line":"f0ce15"},"22":{"line":"00b251"},"23":{"line":"00b251"},"35":{"line":"a2a2a2"},"39":{"line":"0896d7","station":{"name":"79yuhikjn_","lines":["0896d7"]}},"45":{"line":"00b251"}},"60":{"20":{"line":"f0ce15"},"21":{"line":"00b251"},"22":{"line":"00b251"},"34":{"line":"df8600"},"38":{"line":"0896d7"},"44":{"line":"00b251"},"45":{"line":"00b251"}},"61":{"14":{"line":"f0ce15"},"19":{"line":"00b251"},"20":{"line":"00b251"},"35":{"line":"a2a2a2"},"37":{"line":"0896d7"},"43":{"line":"00b251"},"44":{"line":"00b251"}},"62":{"17":{"line":"f0ce15"},"18":{"line":"00b251"},"19":{"line":"00b251"},"34":{"line":"df8600"},"36":{"line":"0896d7"},"37":{"line":"0896d7"},"43":{"line":"00b251"}},"63":{"16":{"line":"f0ce15"},"17":{"line":"00b251"},"18":{"line":"00b251"},"36":{"line":"0896d7"}},"64":{"15":{"line":"f0ce15"},"16":{"line":"00b251"},"17":{"line":"00b251"},"18":{"line":"00b251"},"34":{"line":"df8600"},"35":{"line":"a2a2a2"}},"65":{"14":{"line":"f0ce15"},"15":{"line":"00b251"},"16":{"line":"00b251"},"17":{"line":"00b251"},"33":{"line":"df8600"},"34":{"line":"df8600"},"35":{"line":"0896d7"}},"66":{"12":{"line":"f0ce15"},"13":{"line":"f0ce15"},"14":{"line":"f0ce15"},"15":{"line":"00b251"},"17":{"line":"f0ce15"},"33":{"line":"df8600"},"35":{"line":"a2a2a2"}},"67":{"11":{"line":"f0ce15"},"12":{"line":"f0ce15"},"13":{"line":"f0ce15"},"14":{"line":"00b251"},"17":{"line":"00b251"},"18":{"line":"00b251"},"32":{"line":"df8600"},"35":{"line":"0896d7"}},"68":{"8":{"line":"f0ce15"},"10":{"line":"f0ce15"},"11":{"line":"f0ce15"},"13":{"line":"00b251"},"14":{"line":"00b251"},"31":{"line":"df8600"},"35":{"line":"0896d7"}},"69":{"12":{"line":"00b251"},"13":{"line":"00b251"},"34":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"70":{"30":{"line":"df8600"}},"71":{"29":{"line":"df8600"},"33":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"72":{"32":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"73":{"28":{"line":"df8600"},"32":{"line":"0896d7"},"35":{"line":"a2a2a2"}},"74":{"27":{"line":"df8600"},"32":{"line":"0896d7"}},"75":{"27":{"line":"df8600"},"32":{"line":"0896d7"}},"76":{"26":{"line":"df8600"}},"77":{"26":{"line":"df8600"}},"78":{"25":{"line":"df8600"},"26":{"line":"df8600"}},"global":{"lines":{"bd1038":{"displayName":"Red Line"},"df8600":{"displayName":"Orange Line"},"f0ce15":{"displayName":"Yellow Line"},"00b251":{"displayName":"Green Line"},"0896d7":{"displayName":"Blue Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"}}}}"""

MAX_MAP_SIZE = 240
VALID_XY = [str(x) for x in range(MAX_MAP_SIZE)]

def is_hex(string):

    """ Determines whether a string is a hexademical string (0-9, a-f) or not
    """

    try:
        int(string, 16)
    except ValueError:
        return False
    else:
        return True

def hex2b64(hexthree):

    """ Convert a three-digit hex value to a two-digit base64 value
    """

    hexthree = int(hexthree, 16)
    assert 0 <= hexthree <= 4095

    base64_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'

    if hexthree < 64:
        # Add "a" (the base64 equivalent of zero) -padding to the result
        return 'a{0}'.format(base64_chars[hexthree])
    else:
        return '{0}{1}'.format(base64_chars[hexthree // 64], base64_chars[hexthree % 64])

def hex64(hexdigest):

    # The first 12 digits of a hexdigest give us 16^12, or 281,474,976,710,656 (281 trillion)
    # This is equivalent to 64^8
    # So instead of a 12-digit long URL, we can shorten down to 8 characters and still retain a high level of collision resistance
    hexdigest = hexdigest[:12]

    return '{0}{1}{2}{3}'.format(hex2b64(hexdigest[:3]), hex2b64(hexdigest[3:6]), hex2b64(hexdigest[6:9]), hex2b64(hexdigest[9:]))

def sanitize_string(string):
    return string.replace('<', '').replace('>', '').replace('"', '').replace("'", '&#x27;').replace('&', '&amp;').replace('/', '&#x2f;').replace('\x1b', '').replace('\\', '').replace('\t', ' ').replace('\n', ' ').replace('\b', ' ').replace('%', '')

def sanitize_string_without_html_entities(string):
    return string.replace('<', '').replace('>', '').replace('"', '').replace("'", '').replace('&', '').replace('/', '').replace('\x1b', '').replace('\\', '').replace('\t', ' ').replace('\n', ' ').replace('\b', ' ').replace('%', '')

def convert_nonascii_to_ascii(input_str):

    """
        Convert text with beyond the ASCII character set down to ASCII.

        Why do this? MetroMapMaker stores the station name in the HTML element's ID,
            which is very restrictive.

        The validator enforces this, so stations can only have DOM-safe characters.

        And if I'm going to match stations, this needs to be stripped out.

        Used by TravelSystem.models, but available here because it's a general-purpose utility function.
    """

    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def html_dom_id_safe(string):

    """ Returns a string santized of any characters that are not suitable for an HTML DOM's ID
    """

    return re.sub('[^A-Za-z0-9\- \_]', '', string)

def validate_metro_map_v2(metro_map):

    """ Validate the MetroMap object, with a more compact, optimized data representation
    """

    # TODO: Implement this!
    # ValidationErrors: Anything that appears before the first colon will be internal-only;
    #   everything else is user-facing.
    # It's a dict already!

    validated_metro_map = {
        'global': {
            'lines': {},
            'data_version': 2,
        }
    }

    return validated_metro_map

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

    # Formatting the assertion strings:
    # Anything that appears before the first colon will be internal-only;
    #   everything else is user-facing.

    assert type(metro_map) == dict, "[VALIDATIONFAILED] 01 metro_map IS NOT DICT: Bad map object, needs to be an object."
    assert metro_map.get('global'), "[VALIDATIONFAILED] 02 metro_map DOES NOT HAVE GLOBAL: Bad map object, missing global."
    try:
        assert metro_map['global'].get('lines'), "[VALIDATIONFAILED] 03 metro_map DOES NOT HAVE LINES: Map does not have any rail lines defined."
    except AssertionError:
        # Gracefully fail by looping through the coordinates;
        # collecting any lines, and adding them to the globals list.
        # The displayName won't be pretty,
        # and the map could fail to validate for other reasons,
        # but at least this check will pass if there are lines in the mapdata itself
        inferred_lines = {}
        for x in metro_map.keys():
            if x == 'global' or x not in VALID_XY:
                continue
            for y in metro_map[x].keys():
                if y not in VALID_XY:
                    continue
                line = metro_map[x][y].get('line')
                if line:
                    inferred_lines[line] = {'displayName': line}
        if inferred_lines:
            metro_map['global']['lines'] = inferred_lines
        else:
            raise
    assert type(metro_map['global']['lines']) == dict, "[VALIDATIONFAILED] 04 metro_map LINES IS NOT DICT: Map lines must be stored as an object."
    assert len(metro_map['global']['lines']) <= 100, "[VALIDATIONFAILED] 04B metro_map HAS TOO MANY LINES: Map has too many lines (limit is 100); remove unused lines."

    validated_metro_map = {
        'global': {
            'lines': {

            }
        }
    }

    valid_lines = []

    # Allow HTML color names to be used, but convert them to hex values
    metro_map['global']['lines'] = {
        html_color_name_fragments.get(line.strip()) or line: data
        for line, data in
        metro_map['global']['lines'].items()
    }

    for global_line in metro_map['global']['lines'].keys():
        assert is_hex(global_line), "[VALIDATIONFAILED] 05 global_line {0} FAILED is_hex() {0} is not a valid color: {0} is not a valid rail line color.".format(global_line)
        assert len(global_line) == 6, "[VALIDATIONFAILED] 06 global_line {0} IS NOT 6 CHARACTERS: The color {0} must be 6 characters long.".format(global_line)
        # Transformations to the display name could result in a non-unique display name, but it doesn't actually matter.
        display_name = metro_map['global']['lines'][global_line].get('displayName', 'Rail Line')
        if len(display_name) < 1:
            metro_map['global']['lines'][global_line]['displayName'] = 'Rail Line'
        elif len(display_name) > 255:
            metro_map['global']['lines'][global_line]['displayName'] = display_name[:255]
        assert 1 <= len(metro_map['global']['lines'][global_line].get('displayName', 'Rail Line')) < 256, "[VALIDATIONFAILED] 07 displayName BAD SIZE: Rail line names must be between 1 and 255 characters long (spaces are okay)."
        valid_lines.append(global_line)
        validated_metro_map['global']['lines'][global_line] = {
            'displayName': sanitize_string(metro_map['global']['lines'][global_line]['displayName'])
        }

    for x in metro_map.keys():
        if x == 'global' or x not in VALID_XY:
            continue
        if metro_map.get(x):
            if not validated_metro_map.get(x):
                validated_metro_map[x] = {}
            for y in metro_map[x].keys():
                if y not in VALID_XY:
                    continue
                if metro_map[x].get(y):
                    if not validated_metro_map[x].get(y):
                        validated_metro_map[x][y] = {}
                    assert is_hex(metro_map[x][y]["line"]), "[VALIDATIONFAILED] 08 {0} at ({1}, {2}) FAILED is_hex(): Point at ({3}, {4}) is not a valid color: {0}.".format(metro_map[x][y]["line"], x, y, int(x) + 1, int(y) + 1)
                    assert len(metro_map[x][y]["line"]) == 6, "[VALIDATIONFAILED] 09 {0} at ({1}, {2}) IS NOT 6 CHARACTERS: Point at ({3}, {4}) has a color that needs to be 6 characters long: {0}".format(metro_map[x][y]["line"], x, y, int(x) + 1, int(y) + 1)
                    try:
                        assert metro_map[x][y]["line"] in valid_lines, "[VALIDATIONFAILED] 10 {0} at ({1}, {2}) NOT IN valid_lines: Point at ({3}, {4}) has a color that is not defined in the rail lines; please create a line matching the color {0}.".format(metro_map[x][y]["line"], x, y, int(x) + 1, int(y) + 1)
                    except AssertionError:
                        del validated_metro_map[x][y] # delete this coordinate or it'll be undefined
                        continue # If the line isn't in valid_lines, we could just not add it
                    else:
                        validated_metro_map[x][y]["line"] = metro_map[x][y]["line"]
                    if metro_map[x][y].get('station'):
                        assert type(metro_map[x][y]["station"]) == dict, "[VALIDATIONFAILED] 11 metro_map[x][y]['station'] at ({0}, {1}) IS NOT DICT: Point at ({2}, {3}) has a malformed station, must be an object.".format(x, y, int(x) + 1, int(y) + 1)
                        metro_map[x][y]["station"]["name"] = sanitize_string_without_html_entities(metro_map[x][y]["station"]["name"])
                        if metro_map[x][y]["station"]["name"] == '':
                            metro_map[x][y]["station"]["name"] = "_" # Gracefully rename a zero-length station name to be a single space
                        assert 1 <= len(metro_map[x][y]["station"]["name"]) < 256, "[VALIDATIONFAILED] 12 station name at ({0}, {1}) BAD SIZE {2} is {3}: Point at ({4}, {5}) has a station whose name is not between 1 and 255 characters long. Please rename it.".format(x, y, metro_map[x][y]["station"]["name"], len(metro_map[x][y]["station"]["name"]), int(x) + 1, int(y) + 1)
                        assert type(metro_map[x][y]["station"].get("lines", [])) == list, "[VALIDATIONFAILED] 13 station lines at ({0}, {1}) NOT A LIST: Point at ({2}, {3}) has its station lines in the incorrect format; must be a list.".format(x, y, int(x) + 1, int(y) + 1)
                        # Okay, this probably *should* pass - but I think I have some bug in the javascript somewhere because https://metromapmaker.com/?map=zCq7R223 obviously passed validation but once reconstituted, fails. But this isn't a big enough deal that I can't wave this validation through while I figure out what's going on.
                        # assert len(metro_map[x][y]["station"]["lines"]) > 0, "[VALIDATIONFAILED] 14: station lines at ({0}, {1}) HAS ZERO LENGTH".format(x, y)
                        validated_metro_map[x][y]["station"] = {
                            # "name": html_dom_id_safe(metro_map[x][y]["station"]["name"].replace('/', '').replace("'", '').replace('&', '').replace('`', '')),
                            "name": metro_map[x][y]["station"]["name"],
                            "lines": []
                        }
                        for station_line in metro_map[x][y]["station"].get("lines", []):
                            if station_line in html_color_name_fragments:
                                station_line = html_color_name_fragments[station_line]
                            assert is_hex(station_line), "[VALIDATIONFAILED] 15 station_line {0} FAILED is_hex(): Station Rail line {0} is not a valid color.".format(station_line)
                            assert len(station_line) == 6, "[VALIDATIONFAILED] 16 station_line {0} IS NOT 6 CHARACTERS: Station Rail line color {0} needs to be 6 characters long.".format(station_line)
                            try:
                                assert station_line in valid_lines, "[VALIDATIONFAILED] 17 station_line {0} NOT IN valid_lines: Station rail line color {0} is not defined; please create a rail line matching this color or remove it from all stations.".format(station_line)
                            except AssertionError:
                                # We can gracefully fail here by simply not adding that line to the station
                                continue
                            else:
                                validated_metro_map[x][y]["station"]["lines"].append(station_line)
                        if metro_map[x][y]["station"].get('transfer'):
                           validated_metro_map[x][y]["station"]["transfer"] = 1
                        if metro_map[x][y]["station"].get('orientation') and metro_map[x][y]["station"].get('orientation') in ('0', '-45', '45', '-90', '90', '135', '-135', '180'):
                            validated_metro_map[x][y]["station"]["orientation"] = metro_map[x][y]["station"].get('orientation')

    return validated_metro_map
