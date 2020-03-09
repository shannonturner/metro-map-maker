import json
import unittest

from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

from map_saver.models import SavedMap

class FrontendFunctionalityTestCase(object):

    """ Selenium testing to confirm that front-end functionality changes do not cause regressions
    """

    website = 'http://127.0.0.1:8000/'

    def setUp(self):
        self.driver.get(self.website)
        # Wait up to two seconds;
        # if rail-line-cfe4a7 (Parks) is loaded, we know we have the default map
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

    def tearDown(self):
        self.driver.close()

    # Leave these helper functions prefixed with helper_
    #   so it's easier to find them all when writing tests
    #   & you won't have to remember all of their names
    def helper_erase_blank_to_save(self):

        """ activeMap begins as false until autoSaved, so erase a blank square to save
        """

        eraser_button = self.driver.find_element_by_id('tool-eraser')
        canvas = self.driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 0, 0)
        action.click()
        action.perform()

    def helper_clear_draw_single_point(self):

        """ Erase the map, then add a single point
        """

        clear_map_button = self.driver.find_element_by_id('tool-clear-map')
        clear_map_button.click()

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        # Click the Red button
        rail_line_button = self.driver.find_element_by_id('rail-line-bd1038')
        rail_line_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 8, 8 since the map was cleared and is now on a smaller grid size
        action.click()
        action.perform()

    def helper_return_image_canvas_data(self):

        """ Getting the image canvas data for comparison is common.
        """

        self.driver.execute_script('drawCanvas(activeMap);')
        map_image = self.driver.execute_script('return combineCanvases().toDataURL();')

        return map_image

    class expected_condition_element_has_attr(object):

        """ An expectation for checking that an element has a particular attribute.
        """

        def __init__(self, element, attr):
            self.element = element
            self.attr = attr

        def __call__(self, driver):
            if self.element.get_attribute(self.attr):
                return self.element.get_attribute(self.attr)
            else:
                return False

    # @unittest.skip(reason='DEBUG')
    def test_loads_default_map(self):

        """ Confirm that the WMATA map loads by default
        """

        parks_rail_line = self.driver.find_element_by_id('rail-line-cfe4a7')
        self.assertTrue(parks_rail_line)

        self.helper_erase_blank_to_save()
        metro_map = self.driver.execute_script("return activeMap;")

        self.assertEqual(
            metro_map['94']['40'],
            {"line":"bd1038","station":{"transfer":1,"lines":["bd1038","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )

        self.assertEqual(
            metro_map['136']['24']['station'],
            {"lines":["a2a2a2"],"name":"Silver_Line_-_Wiehle-Reston_East_to_Largo","orientation":"0"}
        )

    # @unittest.skip(reason='DEBUG')
    def test_subsequent_loads_saved_map(self):

        """ Confirms that subsequent page loads will load the map saved in localstorage rather than the default WMATA map
        """

        # First, confirm that we've loaded the default WMATA map by checking for Fort Totten
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )
        self.helper_erase_blank_to_save()
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40'],
            {"line":"bd1038","station":{"transfer":1,"lines":["bd1038","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )

        # Next, clear the map and reload the page
        self.helper_clear_draw_single_point()
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )
        self.helper_erase_blank_to_save()
        metro_map = self.driver.execute_script("return activeMap;")

        self.assertFalse(metro_map.get('94'))
        self.assertEqual(
            metro_map['8']['8'],
            {"line": "bd1038"},
        )

    # @unittest.skip(reason='DEBUG')
    def test_bad_url_hash(self):

        """ Confirm that the grid loads and the rail lines are bound even if the provided URLhash was bad
        """
        bad_url_hashes = [
            '000BADMAP000_001', # no map at this hash
            '`000BADMAP000%%%_002', # malformed urlhash
            '', # missing urlhash
        ]

        for index, bad_hash in enumerate(bad_url_hashes):
            self.driver.get(f'{self.website}?map={bad_hash}')

            WebDriverWait(self.driver, 2).until(
                expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
            )

            rail_line_menu_button = self.driver.find_element_by_id('tool-line')
            rail_line_menu_button.click()

            red_line_button = self.driver.find_element_by_id('rail-line-bd1038')
            red_line_button.click()

            canvas = self.driver.find_element_by_id('metro-map-canvas')

            # Click on the canvas at 100,100
            action = webdriver.common.action_chains.ActionChains(self.driver)
            action.move_to_element_with_offset(canvas, 100, 100 + (index * 6)) # 17, 17
            action.click()
            action.perform()

            # Confirm that there is a line painted at the expected coordinates
            self.helper_erase_blank_to_save()
            metro_map = self.driver.execute_script("return activeMap;")
            self.assertEqual(
                metro_map['17'][str(17 + index)],
                {'line': 'bd1038'},
            )

    # @unittest.skip(reason='DEBUG')
    def test_expand_collapse_rail_line_menu(self):

        """ Confirm that clicking Draw Rail Line will expand/hide the available rail lines
        """

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_lines = self.driver.find_elements_by_class_name('rail-line')

        # Rail lines begin hidden
        for line in rail_lines:
            self.assertFalse(line.is_displayed())

        # Rail lines are revealed when the menu button is clicked
        rail_line_menu_button.click()
        for line in rail_lines:
            self.assertTrue(line.is_displayed())

        # Rail lines are hidden once again when the menu button is clicked again
        rail_line_menu_button.click()
        for line in rail_lines:
            self.assertFalse(line.is_displayed())

        # Keyboard shortcut: D to hide/reveal Draw Rail Lines
        body = self.driver.find_element_by_xpath("//body")
        body.send_keys('d')
        for line in rail_lines:
            self.assertTrue(line.is_displayed())

        body.send_keys('d')
        for line in rail_lines:
            self.assertFalse(line.is_displayed())

    # @unittest.skip(reason='DEBUG')
    def test_paint_rail_line(self):

        """ Confirm that painting a rail line on the canvas stores that data in activeMap
        """

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        # Get image canvas data for comparison later
        map_image = self.helper_return_image_canvas_data()

        # Click the Red button
        rail_line_button = self.driver.find_element_by_id('rail-line-bd1038')
        rail_line_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['17'],
            {'line': 'bd1038'},
        )

        # Click and drag
        # First, change the color (helps debugging)
        rail_line_button = self.driver.find_element_by_id('rail-line-0896d7')
        rail_line_button.click()
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 120, 100) # 20, 17
        action.click()
        action.click_and_hold()
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.release()
        action.perform()

        metro_map = self.driver.execute_script("return activeMap;")
        for col in range(17, 21): # 17, 18, 19, 20
            self.assertEqual(
                metro_map['20'][str(col)],
                {'line': '0896d7'}
            )

        new_map_image = self.helper_return_image_canvas_data()

        self.assertNotEqual(map_image, new_map_image)

    # @unittest.skip(reason='DEBUG')
    def test_overpaint_rail_line(self):

        """ Confirm that painting over a coordinate with a different color will overwrite it
        """

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        # Click the Red button
        rail_line_button = self.driver.find_element_by_id('rail-line-bd1038')
        rail_line_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['17'],
            {'line': 'bd1038'},
        )

        # Get image canvas data for later comparison
        map_image = self.helper_return_image_canvas_data()

        # Click the Blue button
        rail_line_button = self.driver.find_element_by_id('rail-line-0896d7')
        rail_line_button.click()

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['17'],
            {'line': '0896d7'},
        )

        new_map_image = self.helper_return_image_canvas_data()
        self.assertNotEqual(map_image, new_map_image)

    # @unittest.skip(reason='DEBUG')
    def test_add_new_line(self):

        """ Confirm that adding a new rail line makes it available in the rail line options and in the global
        """

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        create_new_line_button = self.driver.find_element_by_id('rail-line-new')
        create_new_line_button.click()

        # I don't know the "correct" way to have Selenium actually click the color, so this will have to suffice
        self.driver.execute_script('document.getElementById("new-rail-line-color").value="#8efa00"')

        new_line_name = self.driver.find_element_by_id('new-rail-line-name')
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.send_keys_to_element(new_line_name, 'Lime Line')
        action.perform()
        save_new_line_button = self.driver.find_element_by_id('create-new-rail-line')
        save_new_line_button.click()

        # Confirm it actually will paint, too
        lime_line_button = self.driver.find_element_by_id('rail-line-8efa00')
        lime_line_button.click()

        # Click on the canvas at 100,100
        canvas = self.driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(self.driver) # Create a new action chains
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['17'],
            {'line': '8efa00'},
        )

        # Confirm it exists in the global
        self.assertEqual(
            metro_map['global']['lines']['8efa00'],
            {'displayName': 'Lime Line'}
        )

    # @unittest.skip(reason='DEBUG')
    def test_delete_unused_lines(self):

        """ Confirm that deleting unused lines only deletes the correct lines, and deletes them from the rail line options and the global
        """

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        self.helper_erase_blank_to_save()
        metro_map = self.driver.execute_script("return activeMap;")

        # Of the defaults, only the purple line is not in use in the default WMATA map
        # Confirm it's there, then delete it
        self.assertEqual(
            metro_map['global']['lines']['662c90'],
            {'displayName': 'Purple Line'}
        )
        purple_line_button = self.driver.find_element_by_id('rail-line-662c90')

        delete_unused_lines_button = self.driver.find_element_by_id('rail-line-delete')
        delete_unused_lines_button.click()

        metro_map = self.driver.execute_script("return activeMap;")

        self.assertFalse(metro_map['global']['lines'].get('662c90'))
        with self.assertRaises(StaleElementReferenceException):
            purple_line_button.click()

        # Confirm the rest of the lines were not deleted
        remaining_lines = ["0896d7", "df8600", "000000", "00b251", "a2a2a2", "f0ce15", "bd1038", "79bde9", "cfe4a7"]
        for line in remaining_lines:
            self.assertTrue(metro_map['global']['lines'][line])
            line_button = self.driver.find_element_by_id(f'rail-line-{line}')

    # @unittest.skip(reason='DEBUG')
    def test_edit_line_colors(self):

        """ Confirm that editing an existing rail line's name and/or color works as intended, replacing all instances in the ui, global, and map data
        """

        # Confirm Ft Totten exists before we change the red line's color
        self.helper_erase_blank_to_save()
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40'],
            {"line":"bd1038","station":{"transfer":1,"lines":["bd1038","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )

        # Count number of times the red line appears
        red_line_mentions = json.dumps(metro_map).count('bd1038')

        # Download the map as an image; after editing the color we'll make sure it's not the same
        map_image = self.helper_return_image_canvas_data()

        # Change the Red Line to the Lime Line
        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        edit_color_button = self.driver.find_element_by_id('rail-line-change')
        edit_color_button.click()

        edit_rail_line_select = Select(self.driver.find_element_by_id('tool-lines-to-change'))
        edit_rail_line_select.select_by_visible_text('Red Line')

        # I don't know the "correct" way to have Selenium actually click the color, so this will have to suffice
        self.driver.execute_script('document.getElementById("change-line-color").value="#8efa00"')

        edit_line_name = self.driver.find_element_by_id('change-line-name')
        edit_line_name.clear()
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.send_keys_to_element(edit_line_name, 'Lime Line')
        action.perform()

        save_rail_line_edits_button = self.driver.find_element_by_id('save-rail-line-edits')
        save_rail_line_edits_button.click()

        # Reload the map and confirm that everything is changed over
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            red_line_mentions,
            json.dumps(metro_map).count('8efa00') # Lime Line mentions
        )
        self.assertEqual(
            0,
            json.dumps(metro_map).count('bd1038') # Red Line mentions in the new map
        )
        self.assertEqual(
            metro_map['94']['40'],
            {"line":"8efa00","station":{"transfer":1,"lines":["8efa00","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )
        self.assertEqual(
            metro_map['global']['lines']['8efa00'],
            {'displayName': 'Lime Line'}
        )
        self.assertFalse(metro_map['global']['lines'].get('bd1038'))

        # Confirm the new map image isn't the same
        new_map_image = self.helper_return_image_canvas_data()

        self.assertNotEqual(
            map_image,
            new_map_image
        )

    # @unittest.skip(reason='DEBUG')
    def test_add_station(self):

        """ Confirm that you can add a station to a coordinate with a rail line
        """

        map_image = self.helper_return_image_canvas_data()

        station_button = self.driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 330) # 17, 55
        action.click()
        # using .send_keys() also confirms that #station-name has been given focus
        action.send_keys('abc').send_keys(Keys.ENTER)
        action.perform()

        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['55']['station']['name'],
            'abc'
        )

        new_map_image = self.helper_return_image_canvas_data()

        self.assertNotEqual(map_image, new_map_image)

    # @unittest.skip(reason='DEBUG')
    def test_station_name_zero_size(self):

        """ Confirm that naming a station (required to place it), then renaming it to zero size, then saving will pass validation and the station will have a single space for its name when the new URL is opened
        """

        self.helper_clear_draw_single_point()

        station_button = self.driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 8, 8
        action.click()
        action.send_keys('abc').send_keys(Keys.ENTER)
        action.perform()

        station_name = self.driver.find_element_by_id('station-name')
        station_name.clear()

        save_map_button = self.driver.find_element_by_id('tool-save-map')
        save_map_button.click()

        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
        )

        map_link = self.driver.find_element_by_id('shareable-map-link').get_attribute('href')
        self.driver.get(f'{map_link}')

        # Wait two seconds until the map has re-loaded
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        station_button = self.driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 8, 8
        action.click()
        action.perform()

        station_name = self.driver.find_element_by_id('station-name')
        self.assertEqual(' ', station_name.get_attribute('value'))

    # @unittest.skip(reason='DEBUG')
    def test_edit_station(self):

        """ Confirm that clicking on an existing station will edit it
        """

        self.helper_erase_blank_to_save()

        station_button = self.driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40']['station']['name'],
            'Fort_Totten'
        )

        # Edit Ft Totten
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 562, 238) # 94, 40
        action.click()
        action.send_keys('abc').send_keys(Keys.ENTER)
        action.perform()

        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40']['station']['name'],
            'Fort_Tottenabc'
        )

    # @unittest.skip(reason='DEBUG')
    def test_noadd_empty_station(self):

        """ Confirm that clicking on a coordinate with a rail line to add a station, then clicking somewhere else will not create the station
        """

        station_button = self.driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 323) # 17, 55
        action.click()
        action.perform()

        # Click to a different coordinate without saving the new station
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        metro_map = self.driver.execute_script("return activeMap;")
        self.assertFalse(
            metro_map['17']['55'].get('station')
        )

    # @unittest.skip(reason='DEBUG')
    def test_noadd_invalid_station_position(self):

        """ Confirm that a station cannot be placed on an empty coordinate
        """

        station_button = self.driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertFalse(metro_map['17'].get('17'))

    # @unittest.skip(reason='DEBUG')
    def test_eraser(self):

        """ Confirm that erasing will delete any station and/or rail line at that coordinate
        """

        # Confirm Ft Totten exists before we delete it
        self.helper_erase_blank_to_save()
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40'],
            {"line":"bd1038","station":{"transfer":1,"lines":["bd1038","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )

        map_image = self.helper_return_image_canvas_data()

        eraser_button = self.driver.find_element_by_id('tool-eraser')
        eraser_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 562, 238) # 94, 40
        action.click()
        action.perform()

        metro_map = self.driver.execute_script("return activeMap;")
        self.assertFalse(
            metro_map['94'].get('40')
        )

        new_map_image = self.helper_return_image_canvas_data()
        self.assertNotEqual(map_image, new_map_image)

    # @unittest.skip(reason='DEBUG')
    def test_keyboard_shortcut_tools(self):

        """ Confirm that keyboard shortcuts work for many tools
        """

        body = self.driver.find_element_by_xpath("//body")

        activeTool = self.driver.execute_script("return activeTool;")
        self.assertEqual(activeTool, 'look')

        # Keyboard shortcut: 0-9 for rail lines
        colors = []
        for key in range(10):
            body.send_keys(f'{key}')
            activeTool = self.driver.execute_script("return activeTool;")
            self.assertEqual(activeTool, 'line')
            activeColor = self.driver.execute_script('return rgb2hex(activeToolOption).slice(1, 7)')
            print(activeColor)
            # Confirm it's a new color each time
            self.assertNotIn(activeColor, colors)
            colors.append(activeColor)

        # Keyboard shortcut: E for eraser
        body.send_keys('e')
        activeTool = self.driver.execute_script("return activeTool;")
        self.assertEqual(activeTool, 'eraser')

        # Keyboard shortcut: S for station
        body.send_keys('s')
        activeTool = self.driver.execute_script("return activeTool;")
        self.assertEqual(activeTool, 'station')

        # Keyboard shortcut: G for straight-line-assist guide
        straight_line_assist_guide = self.driver.find_element_by_id('straight-line-assist')
        body.send_keys('g')
        self.assertFalse(straight_line_assist_guide.get_attribute('checked'))
        body.send_keys('g')
        self.assertTrue(straight_line_assist_guide.get_attribute('checked'))

    # @unittest.skip(reason='DEBUG')
    def test_download_as_image(self):

        """ Confirm that clicking download as image creates a download link
        """

        # The image download link does not have an href yet
        image_download_link = self.driver.find_element_by_id('metro-map-image-download-link')
        self.assertFalse(image_download_link.get_attribute('href'))

        download_as_image_button = self.driver.find_element_by_id('tool-download-image')
        download_as_image_button.click()

        # Confirm that the download link now has an href
        WebDriverWait(self.driver, 2).until(
            self.expected_condition_element_has_attr(image_download_link, 'href')
        )
        self.assertTrue(image_download_link.get_attribute('href'))

    # @unittest.skip(reason='DEBUG')
    def test_save_share_map(self):

        """ Confirm that clicking Save and Share map will generate a unique URL based on the mapdata, and visiting that URL contains a map with that data
        """

        self.helper_clear_draw_single_point()

        # Download the map as an image for comparing later
        map_image = self.helper_return_image_canvas_data()

        save_map_button = self.driver.find_element_by_id('tool-save-map')
        save_map_button.click()

        WebDriverWait(self.driver, 1).until(
            expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
        )

        map_link = self.driver.find_element_by_id('shareable-map-link').get_attribute('href')
        metro_map = self.driver.execute_script("return activeMap;")

        self.driver.get(f'{map_link}')

        # Wait two seconds until the map has re-loaded
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        self.helper_erase_blank_to_save()
        new_metro_map = self.driver.execute_script("return activeMap;")

        self.assertEqual(metro_map, new_metro_map)

        new_map_image = self.helper_return_image_canvas_data()

        self.assertEqual(map_image, new_map_image)

    # @unittest.skip(reason='DEBUG')
    def test_save_share_map_no_overwrite(self):

        """ Confirm that clicking Save and Share map multiple times return the same urlhash
        """

        # Note: test_validation's test_valid_map_saves() also confirms
        #   that multiple posts with the same data do not overwrite
        #   the original mapdata or urlhash

        self.helper_clear_draw_single_point()
        save_map_button = self.driver.find_element_by_id('tool-save-map')

        map_links = set()

        for attempt in range(5):
            save_map_button.click()

            WebDriverWait(self.driver, 2).until(
                expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
            )

            map_link = self.driver.find_element_by_id('shareable-map-link').get_attribute('href')
            map_links.add(map_link)

            # Prevent state elements by making sure we delete it in between saves
            self.driver.execute_script("document.getElementById('shareable-map-link').remove()")

        self.assertEqual(
            1,
            len(map_links)
        )

    # @unittest.skip(reason='DEBUG')
    def test_name_map(self):

        """ Confirm that a newly-created map can be named
        """

        # Note: Since Selenium tests use the browser, created maps go into the (production) database,
        #   NOT into the testing database.
        # As a result, I can't use SavedMap.objects.get() here after clicking #tool-save-map
        # But this is okay - I'm using test_validation's test_valid_map_saves() to confirm that the backend responds properly.

        self.helper_clear_draw_single_point()
        save_button = self.driver.find_element_by_id('tool-save-map')
        save_button.click()
        
        WebDriverWait(self.driver, 1).until(
            expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
        )

        map_link = self.driver.find_element_by_id('shareable-map-link')
        self.assertTrue(map_link.text)

        map_name = self.driver.find_element_by_id('user-given-map-name')
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.send_keys_to_element(map_name, 'single dot', Keys.ENTER)
        action.perform()

        name_map_button = self.driver.find_element_by_id('name-this-map')
        name_map_button.click()

        WebDriverWait(self.driver, 2).until(
            expected_conditions.invisibility_of_element((By.ID, 'name-this-map'))
        )

        self.assertEqual(
            'display: none;',
            name_map_button.get_attribute('style')
        )

    # @unittest.skip(reason='DEBUG')
    def test_name_map_subsequent(self):

        """ Confirm that subsequent clicks to Save and Share map will remember what you named your previous map
        """

        self.helper_clear_draw_single_point()

        blue_line_button = self.driver.find_element_by_id('rail-line-0896d7')
        blue_line_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')

        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 200, 200)
        action.click()
        action.perform()

        save_button = self.driver.find_element_by_id('tool-save-map')
        save_button.click()

        WebDriverWait(self.driver, 1).until(
            expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
        )

        map_link = self.driver.find_element_by_id('shareable-map-link')
        self.assertTrue(map_link.text)

        map_name = self.driver.find_element_by_id('user-given-map-name')
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.send_keys_to_element(map_name, 'test_name_map_subsequent', Keys.ENTER)
        action.perform()

        name_map_button = self.driver.find_element_by_id('name-this-map')
        name_map_button.click()

        WebDriverWait(self.driver, 2).until(
            expected_conditions.invisibility_of_element((By.ID, 'name-this-map'))
        )

        # Now draw another mark and re-click the save button
        blue_line_button.click()
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 100, 200)
        action.click()
        action.perform()
        save_button.click()

        WebDriverWait(self.driver, 2).until(
            expected_conditions.visibility_of_element_located((By.ID, "user-given-map-name"))
        )

        # Confirm that the text input and tag dropdown both show if only the name was entered
        map_name = self.driver.find_element_by_id('user-given-map-name')
        map_name.click()
        map_tags = Select(self.driver.find_element_by_id('user-given-map-tags'))
        map_tags.select_by_visible_text('This is a real metro system')
        name_map_button = self.driver.find_element_by_id('name-this-map')
        name_map_button.click()

        # Now draw a final mark and re-click the save button
        blue_line_button.click()
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 50, 50)
        action.click()
        action.perform()
        save_button.click()

        # Confirm that the previous map's name and tags were remembered
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "map-somewhere-else"))
        )
        remembered_map_name = self.driver.find_element_by_id('map-somewhere-else')
        self.assertEqual(
            'Not a map of test_name_map_subsequent? Click here to rename',
            remembered_map_name.text
        )

    # @unittest.skip(reason='DEBUG')
    def test_name_map_no_overwrite(self):

        """ Confirm that a map that is named by an admin cannot be overwritten by a visitor
        """

        self.driver.get(f'{self.website}?map=y87c6hf7') # Washington, DC

        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        save_button = self.driver.find_element_by_id('tool-save-map')
        save_button.click()

        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
        )

        map_link = self.driver.find_element_by_id('shareable-map-link')
        self.assertTrue(map_link.text)

        # There's no option given to allow the user to name this, since it already has an admin-given name
        with self.assertRaises(NoSuchElementException):
            map_name = self.driver.find_element_by_id('user-given-map-name')

    # @unittest.skip(reason='DEBUG')
    def test_show_hide_grid(self):

        """ Confirm that showing/hiding the grid works correctly
        """

        # Test by looking for the opacity change of the grid-canvas

        grid_button = self.driver.find_element_by_id('tool-grid')
        grid_canvas = self.driver.find_element_by_id('grid-canvas')

        # Grid begins visible
        self.assertEqual(
            1,
            int(grid_canvas.value_of_css_property('opacity'))
        )

        # First click hides the grid
        grid_button.click()
        self.assertEqual(
            0,
            int(grid_canvas.value_of_css_property('opacity'))
        )

        # Next click shows it again
        grid_button.click()
        self.assertEqual(
            1,
            int(grid_canvas.value_of_css_property('opacity'))
        )

        # Keyboard shortcut: H to hide the grid
        body = self.driver.find_element_by_xpath("//body")
        body.send_keys('h')
        self.assertEqual(0, int(grid_canvas.value_of_css_property('opacity')))

        # Show it again
        body.send_keys('h')
        self.assertEqual(1, int(grid_canvas.value_of_css_property('opacity')))

    # @unittest.skip(reason='DEBUG')
    def test_zoom_in(self):

        """ Confirm that zooming in resizes the canvas container and eventually shows the Snap to Left button
        """

        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        canvas_container = self.driver.find_element_by_id('canvas-container')
        columns = self.driver.execute_script("return gridCols;")
        width = int(canvas_container.value_of_css_property('width')[:-2])
        snap_controls_button = self.driver.find_element_by_id('snap-controls-left')

        zoom_in_button = self.driver.find_element_by_id('tool-zoom-in')
        zoom_in_button.click()

        new_width = int(canvas_container.value_of_css_property('width')[:-2])
        self.assertEqual(
            columns + width,
            new_width
        )

        # The Snap Controls to Left button isn't here yet, but will be in one more zoom
        self.assertEqual(
            'none',
            snap_controls_button.value_of_css_property('display')
        )

        zoom_in_button.click()
        new_width = int(canvas_container.value_of_css_property('width')[:-2])
        self.assertEqual(
            (columns * 2) + width,
            new_width
        )
        self.assertEqual(
            'block',
            snap_controls_button.value_of_css_property('display')
        )

        # Keyboard shortcut: = to zoom in
        width = int(canvas_container.value_of_css_property('width')[:-2])
        body = self.driver.find_element_by_xpath("//body")
        body.send_keys('=')

        new_width = int(canvas_container.value_of_css_property('width')[:-2])
        self.assertGreater(new_width, width)

    # @unittest.skip(reason='DEBUG')
    def test_zoom_out(self):

        """ Confirm that zooming out resizes the canvas container
        """

        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        canvas_container = self.driver.find_element_by_id('canvas-container')
        columns = self.driver.execute_script("return gridCols;")
        width = int(canvas_container.value_of_css_property('width')[:-2])

        zoom_out_button = self.driver.find_element_by_id('tool-zoom-out')
        zoom_out_button.click()

        new_width = int(canvas_container.value_of_css_property('width')[:-2])
        self.assertEqual(
            width - columns,
            new_width
        )

        # Confirm that zooming out again won't go below 800 pixels
        zoom_out_button.click()
        new_width = int(canvas_container.value_of_css_property('width')[:-2])
        self.assertEqual(
            800,
            new_width
        )

        # Zoom in a bunch so we can zoom out again
        body = self.driver.find_element_by_xpath("//body")
        body.send_keys('=====')
        width = int(canvas_container.value_of_css_property('width')[:-2])

        # Keyboard shortcut: - to zoom out
        body.send_keys('-')
        new_width = int(canvas_container.value_of_css_property('width')[:-2])
        self.assertLess(new_width, width)

    # @unittest.skip(reason='DEBUG')
    def test_snap_left_right(self):

        """ Confirm that the Snap Controls to Left/Right buttons correctly move the toolbox
        """

        canvas_container = self.driver.find_element_by_id('canvas-container')
        columns = self.driver.execute_script("return gridCols;")
        width = int(canvas_container.value_of_css_property('width')[:-2])
        snap_controls_left_button = self.driver.find_element_by_id('snap-controls-left')
        snap_controls_right_button = self.driver.find_element_by_id('snap-controls-right')

        zoom_in_button = self.driver.find_element_by_id('tool-zoom-in')
        zoom_in_button.click()
        zoom_in_button.click() # snap controls button appears in two zooms

        self.assertEqual(
            'block',
            snap_controls_left_button.value_of_css_property('display')
        )

        # Controls begins pinned to the right
        controls = self.driver.find_element_by_id('controls')
        self.assertEqual(
            '5px',
            controls.value_of_css_property('right')
        )

        # After clicked, the controls snap to the left
        snap_controls_left_button.click()
        self.assertEqual(
            '5px',
            controls.value_of_css_property('left')
        )
        self.assertEqual(
            '995px',
            controls.value_of_css_property('right')
        )

        # Clicking again snaps it back to the right
        snap_controls_right_button.click()
        self.assertEqual(
            '5px',
            controls.value_of_css_property('right')
        )
        self.assertEqual(
            '995px',
            controls.value_of_css_property('left')
        )

    # @unittest.skip(reason='DEBUG')
    def test_move_map(self):

        """ Confirm that using the "Move map" feature moves the painted rail lines and stations as expected
        """

        self.helper_clear_draw_single_point()
        move_menu_button = self.driver.find_element_by_id('tool-move-all')
        move_menu_button.click()

        directions = ['up', 'down', 'left', 'right']

        move_buttons = {direction: self.driver.find_element_by_id(f'tool-move-{direction}') for direction in directions}

        # Initial state: 8,8
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['8'])

        move_buttons['up'].click()
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['7'])

        move_buttons['right'].click()
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['9']['7'])

        move_buttons['down'].click()
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['9']['8'])

        move_buttons['left'].click()
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['8'])

        # Keyboard shortcuts: arrow keys
        body = self.driver.find_element_by_xpath("//body")
        body.send_keys(Keys.DOWN)
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['9'])

        body.send_keys(Keys.UP)
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['8'])

        body.send_keys(Keys.RIGHT)
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['9']['8'])

        body.send_keys(Keys.LEFT)
        metro_map = self.driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['8'])

        # Confirm that moving a point off the grid deletes it
        for click in range(1,9):
            move_buttons['left'].click()
            metro_map = self.driver.execute_script('return activeMap;')
            self.assertTrue(
                metro_map[str(8 - click)]['8']
            )
        else:
            move_buttons['left'].click()
            metro_map = self.driver.execute_script('return activeMap;')
            self.assertFalse(metro_map.get('0')) # 0,8 was the last coordinate

    # @unittest.skip(reason='DEBUG')
    def test_resize_grid(self):

        """ Confirm that resizing the grid expands / contracts as expected; truncating the map data if necessary
        """

        # Default WMATA map is 160x160
        # Confirm initial state
        self.helper_erase_blank_to_save()
        metro_map = self.driver.execute_script("return activeMap;")
        grid_cols = self.driver.execute_script("return gridCols;")
        grid_rows = self.driver.execute_script("return gridRows;")

        # Download the map as an image; after resizing we'll make sure it's not the same
        map_image = self.helper_return_image_canvas_data()

        self.assertEqual(grid_cols, grid_rows)
        self.assertEqual(grid_cols, 160)

        resize_menu_button = self.driver.find_element_by_id('tool-resize-all')
        resize_menu_button.click()

        sizes = [240, 200, 160, 120, 80, 120, 160, 200, 240]
        for size in sizes:
            resize_button = self.driver.find_element_by_id(f'tool-resize-{size}')
            resize_button.click()
            grid_cols = self.driver.execute_script("return gridCols;")
            grid_rows = self.driver.execute_script("return gridRows;")
            self.assertEqual(grid_cols, grid_rows)
            self.assertEqual(grid_cols, size)
            self.assertEqual(
                resize_button.text,
                f'Current Size ({size}x{size})'
            )

            # Confirm that the data has been deleted when sizing down
            self.helper_erase_blank_to_save() # requires we save in the first place
            metro_map = self.driver.execute_script("return activeMap;")
            metro_map.pop('global')
            self.assertTrue(max([int(k) for k in metro_map.keys()]) < size)
            for x in metro_map:
                self.assertTrue(max([int(k) for k in metro_map[x].keys()]) < size)

            # Confirm the map canvas has changed
            new_map_image = self.helper_return_image_canvas_data()
            self.assertNotEqual(
                map_image,
                new_map_image
            )
            # Set the current map image to be the new standard for comparison
            #   That way, we know it always changes
            map_image = new_map_image

    # @unittest.skip(reason='DEBUG')
    def test_resize_grid_saved(self):

        """ Confirm that reloading the map will size down to the smallest viable grid (does not recenter the map to do this)
        """

        # Default WMATA map is 160x160

        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-bd1038"))
        )

        resize_menu_button = self.driver.find_element_by_id('tool-resize-all')
        resize_menu_button.click()
        resize_button = self.driver.find_element_by_id('tool-resize-240')
        resize_button.click()

        # Create a metro map that has strategically-placed dots; when erased and the page is reloaded, the map should size down accordingly.
        metro_map = {
            "global": {"lines": {"bd1038": {"displayName": "Red Line"} } },
            "10": {
                "10": {"line": "bd1038"}, # just here to look pretty
                "80": {"line": "bd1038"}, # forces map to 120x120
                "120": {"line": "bd1038"}, # forces map to 160x160
                "160": {"line": "bd1038"}, # forces map to 200x200
                "200": {"line": "bd1038"}, # forces map to 240x240
            }
        }
        metro_map = json.dumps(metro_map)

        self.driver.execute_script(f"activeMap = '{metro_map}'; autoSave(activeMap); drawCanvas(activeMap);")
        self.driver.get(self.website)
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-bd1038"))
        )

        # # Download the map as an image; after reloading we'll make sure it's not the same
        map_image = self.helper_return_image_canvas_data()

        sizes = [200, 160, 120, 80]
        for size in sizes:

            grid_cols = self.driver.execute_script('return gridCols;')
            grid_rows = self.driver.execute_script('return gridRows;')

            self.assertEqual(grid_cols, grid_rows)
            self.assertEqual(grid_cols, size + 40) # we haven't sized down yet

            resize_menu_button = self.driver.find_element_by_id('tool-resize-all')
            resize_menu_button.click()
            resize_button = self.driver.find_element_by_id(f'tool-resize-{size}')
            resize_button.click()

            # Save the map to localStorage and reload
            self.driver.execute_script('autoSave(activeMap);') # oddly, erase_blank_to_save is not saving here

            self.driver.get(self.website)
            WebDriverWait(self.driver, 2).until(
                expected_conditions.presence_of_element_located((By.ID, "rail-line-bd1038"))
            )

            # Confirm the map canvas has changed
            new_map_image = self.helper_return_image_canvas_data()
            self.assertNotEqual(
                map_image,
                new_map_image,
                'map_image is identical to new_map_image'
            )

            # Set the current map image to be the new standard for comparison
            #   That way, we know it always changes
            map_image = new_map_image

    # @unittest.skip(reason='DEBUG')
    def test_clear_map(self):

        """ Confirm that clicking Clear Map will delete all coordinate data
        """

        self.helper_erase_blank_to_save()

        # Now activeMap has a value of the existing map
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertTrue(type(metro_map) == dict, type(metro_map))
        self.assertTrue(len(metro_map) > 100) # default WMATA has ~140

        clear_map_button = self.driver.find_element_by_id('tool-clear-map')
        clear_map_button.click()

        metro_map = self.driver.execute_script("return activeMap;")
        self.assertTrue(type(metro_map) == dict, type(metro_map))
        self.assertTrue(len(metro_map) == 1)
        self.assertTrue(metro_map["global"]["lines"]) # Confirm that the lines still exist

    # @unittest.skip(reason='DEBUG')
    def test_clear_delete_lines_refresh(self):

        """ Confirm that the default rail lines will be loaded when clearing map, then deleting the rail lines, then saving the map and reloading the page
        """

        clear_map_button = self.driver.find_element_by_id('tool-clear-map')
        clear_map_button.click()

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        red_line_button = self.driver.find_element_by_id('rail-line-bd1038')

        delete_unused_lines_button = self.driver.find_element_by_id('rail-line-delete')
        delete_unused_lines_button.click()

        self.helper_erase_blank_to_save()
        tool_line_options_length = self.driver.execute_script("return document.getElementById('tool-line-options').children.length")

        # Other children besides the rail lines themselves are the add/edit/delete line buttons, straight line assist, etc
        self.assertEqual(
            7,
            tool_line_options_length
        )

        with self.assertRaises(StaleElementReferenceException):
            red_line_button.click()

        # Reload the page
        self.driver.get(self.website)
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-bd1038"))
        )

        red_line_button = self.driver.find_element_by_id('rail-line-bd1038')
        tool_line_options_length = self.driver.execute_script("return document.getElementById('tool-line-options').children.length")

        # Other children besides the rail lines themselves are the add/edit/delete line buttons, etc
        self.assertEqual(
            17,
            tool_line_options_length
        )

    # @unittest.skip(reason='DEBUG')
    def test_undo(self):

        """ Confirm that the undo function works
            and leaves the map in a valid, save-able state
        """

        self.helper_erase_blank_to_save()

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(self.driver)

        # Click and drag
        rail_line_button = self.driver.find_element_by_id('rail-line-0896d7')
        rail_line_button.click()
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 120, 100) # 20, 17
        action.click()
        action.click_and_hold()
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.release()
        action.perform()

        metro_map = self.driver.execute_script("return activeMap;")
        for col in range(17, 21): # 17, 18, 19, 20
            self.assertEqual(
                metro_map['20'][str(col)],
                {'line': '0896d7'}
            )

        # Undo will shrink the line
        for undo in range(3):
            last_metro_map = dict(metro_map)
            self.driver.execute_script("undo();")
            metro_map = self.driver.execute_script("return activeMap;")
            self.assertNotEqual(last_metro_map, metro_map)

        # Confirm the map is in a valid, saveable state
        save_map_button = self.driver.find_element_by_id('tool-save-map')
        save_map_button.click()
        WebDriverWait(self.driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
        )

    # @unittest.skip(reason='DEBUG')
    def test_draw_straight_lines(self):

        """ Confirm that assisted-straight-line drawing
            prevents stray marks, but can also be disabled
        """

        self.helper_erase_blank_to_save()

        self.driver.execute_script("document.getElementById('straight-line-assist').checked = true;")

        rail_line_menu_button = self.driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        canvas = self.driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(self.driver)

        # Click and drag
        rail_line_button = self.driver.find_element_by_id('rail-line-0896d7')
        rail_line_button.click()
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 120, 100) # 20, 17
        action.click()
        action.click_and_hold()
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(5, 5) # Stray
        action.release()
        action.perform()

        metro_map = self.driver.execute_script("return activeMap;")
        for col in range(17, 21): # 17, 18, 19, 20
            self.assertEqual(
                metro_map['20'][str(col)],
                {'line': '0896d7'}
            )
        # Confirm the stray line is not marked
        self.assertFalse(metro_map['21'].get('21', {}))

        # Disable straight line drawing
        # First, change the color (helps debugging)
        rail_line_button = self.driver.find_element_by_id('rail-line-bd1038')
        rail_line_button.click()
        self.driver.execute_script("document.getElementById('straight-line-assist').checked = false;")
        action = webdriver.common.action_chains.ActionChains(self.driver)
        action.move_to_element_with_offset(canvas, 120, 100) # 20, 17
        action.click()
        action.click_and_hold()
        action.move_by_offset(0, 5)
        action.move_by_offset(5, 5)
        action.move_by_offset(5, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(5, 5)
        action.release()
        action.perform()

        # Confirm all the "stray" lines are marked
        metro_map = self.driver.execute_script("return activeMap;")
        self.assertEqual(metro_map['20']['17'], {'line': 'bd1038'})
        self.assertEqual(metro_map['20']['18'], {'line': 'bd1038'})
        self.assertEqual(metro_map['21']['18'], {'line': 'bd1038'})
        self.assertEqual(metro_map['22']['19'], {'line': 'bd1038'})
        self.assertEqual(metro_map['22']['20'], {'line': 'bd1038'})
        self.assertEqual(metro_map['23']['21'], {'line': 'bd1038'})

    def test_mobile_edit_map_anyway(self):

        """ Confirm that on mobile, the map controls appear hidden initially,
            but can be revealed, hiding the 'Edit this map on mobile anyway' button
        """

        self.driver.set_window_size(600, 600)

        edit_on_mobile_button = self.driver.find_element_by_id('try-on-mobile')

        # Controls start off hidden
        controls = self.driver.find_element_by_id('controls')
        self.assertEqual(
            controls.value_of_css_property('display'),
            'none',
        )

        # After clicking, the controls are shown and the button disappears
        edit_on_mobile_button.click()
        self.assertEqual(
            edit_on_mobile_button.value_of_css_property('display'),
            'none',
        )
        self.assertEqual(
            controls.value_of_css_property('display'),
            'block',
        )

    def test_mobile_resize_reenables_disabled_buttons(self):

        """ Confirm that starting on mobile,
            then clicking the (mobile) download as image button (#tool-export-canvas)
            (which works differently on mobile and disables the other buttons)
            then resizing the window, will re-enable the disabled buttons
        """

        self.driver.set_window_size(600, 600)
        edit_on_mobile_button = self.driver.find_element_by_id('try-on-mobile')
        # After clicking, the controls are shown and the button disappears
        edit_on_mobile_button.click()
        self.assertEqual(
            edit_on_mobile_button.value_of_css_property('display'),
            'none',
        )
        # Click the download as image button (mobile)
        # and confirm the rail line button is disabled
        download_as_image_button = self.driver.find_element_by_id('tool-export-canvas')
        download_as_image_button.click()
        rail_line_button = self.driver.find_element_by_id('tool-line')
        WebDriverWait(self.driver, 2).until(
            self.expected_condition_element_has_attr(rail_line_button, 'disabled')
        )
        rail_line_button_is_disabled = self.driver.execute_script("return document.getElementById('tool-line').disabled;")
        self.assertTrue(rail_line_button_is_disabled)

        # Resizing the window above the mobile breakpoint will re-enable the buttons
        self.driver.set_window_size(769, 600)
        rail_line_button_is_disabled = self.driver.execute_script("return document.getElementById('tool-line').disabled;")
        self.assertFalse(rail_line_button_is_disabled)

    def test_mobile_resize_tooltip_direction(self):

        """ Confirm that starting on mobile,
            the tooltips display above the buttons;
            that resizing to a larger screen moves the tooltips to the left;
            and resizing again to mobile puts the tooltips above again
        """

        self.driver.set_window_size(600, 600)
        edit_on_mobile_button = self.driver.find_element_by_id('try-on-mobile')
        # After clicking, the controls are shown and the button disappears
        edit_on_mobile_button.click()

        tooltip_placement = self.driver.execute_script("return $('.has-tooltip').data('bs.tooltip').options.placement;")
        self.assertEqual("top", tooltip_placement)

        # Resizing the window above the mobile breakpoint will re-enable the buttons
        self.driver.set_window_size(769, 600)
        tooltip_placement = self.driver.execute_script("return $('.has-tooltip').data('bs.tooltip').options.placement;")
        self.assertEqual("left", tooltip_placement)

        self.driver.set_window_size(600, 600)
        tooltip_placement = self.driver.execute_script("return $('.has-tooltip').data('bs.tooltip').options.placement;")
        self.assertEqual("top", tooltip_placement)


class ChromeFrontendFunctionalityTestCase(FrontendFunctionalityTestCase, TestCase):

    """ Inherit all tests, use Chrome to perform them
    """

    def setUp(self):
        # Set w3c to False because I was getting the same
        # selenium.common.exceptions.MoveTargetOutOfBoundsException: Message: move target out of bounds
        # I was getting on Firefox; maybe by figuring out how to set
        #   w3c to False on Firefox I could then run those tests too
        # But that doesn't seem like an available option
        # and probably a higher priority is figuring out how to avoid that error in the first place?
        options = webdriver.ChromeOptions()
        options.add_experimental_option('w3c', False)
        self.driver = webdriver.Chrome(chrome_options=options)
        super().setUp()

# class FirefoxFrontendFunctionalityTestCase(FrontendFunctionalityTestCase, TestCase):

#     """ NOT IN USE:
#             Currently fails most tests because geckodriver does not scrollIntoView
#             & they won't fix it because it's not officialy in spec:
#             https://github.com/mozilla/geckodriver/issues/776
#     """

#     def setUp(self):
#         self.driver = webdriver.Firefox()
#         super().setUp()

# class SafariFrontendFunctionalityTestCase(FrontendFunctionalityTestCase, TestCase):

#     """ NOT IN USE:
#             Currently fails most tests because Safari self.driver has issues
#                 with the pause key_action & the workaround didn't work for me
#     """

    # def setUp(self):
    #     self.driver = webdriver.Safari()
    #     super().setUp()
