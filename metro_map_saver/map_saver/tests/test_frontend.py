import json
import unittest

from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import StaleElementReferenceException

from map_saver.models import SavedMap

class FrontendFunctionalityTestCase(TestCase):

    """ Selenium testing to confirm that front-end functionality changes do not cause regressions
    """

    website = 'http://127.0.0.1:8000/'

    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.close()

    def helper_erase_blank_to_save(self, driver):

        """ activeMap begins as false until autoSaved, so erase a blank square to save
        """

        eraser_button = driver.find_element_by_id('tool-eraser')
        canvas = driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 0, 0)
        action.click()
        action.perform()

    def helper_clear_draw_single_point(self, driver):

        """ Erase the map, then add a single point
        """

        clear_map_button = driver.find_element_by_id('tool-clear-map')
        clear_map_button.click()

        rail_line_menu_button = driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        # Click the Red button
        rail_line_button = driver.find_element_by_id('rail-line-bd1038')
        rail_line_button.click()

        canvas = driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 8, 8 since the map was cleared and is now on a smaller grid size
        action.click()
        action.perform()

    @unittest.skip(reason="GOOD")
    def test_loads_default_map(self):

        """ Confirm that the WMATA map loads by default
        """

        driver = self.driver
        driver.get(self.website)

        # Wait up to two seconds;
        # if rail-line-cfe4a7 (Parks) is loaded, we know we have the default map
        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        parks_rail_line = driver.find_element_by_id('rail-line-cfe4a7')
        self.assertTrue(parks_rail_line)

        metro_map = driver.execute_script("return activeMap;")

        self.assertEqual(
            metro_map['94']['40'],
            {"line":"bd1038","station":{"transfer":1,"lines":["bd1038","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )

        self.assertEqual(
            metro_map['136']['24']['station'],
            {"lines":["a2a2a2"],"name":"Silver_Line_-_Wiehle-Reston_East_to_Largo","orientation":"0"}
        )

    @unittest.skip(reason='GOOD')
    def test_subsequent_loads_saved_map(self):

        """ Confirms that subsequent page loads will load the map saved in localstorage rather than the default WMATA map
        """

        driver = self.driver
        driver.get(self.website)

        # First, confirm that we've loaded the default WMATA map by checking for Fort Totten
        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )
        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40'],
            {"line":"bd1038","station":{"transfer":1,"lines":["bd1038","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )

        # Next, clear the map and reload the page
        self.helper_clear_draw_single_point(driver)
        driver.get(self.website)

        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )
        metro_map = driver.execute_script("return activeMap;")

        self.assertFalse(metro_map.get('94'))
        self.assertEqual(
            metro_map['8']['8'],
            {"line": "bd1038"},
        )

    @unittest.skip(reason="GOOD")
    def test_expand_collapse_rail_line_menu(self):

        """ Confirm that clicking Draw Rail Line will expand/hide the available rail lines
        """

        driver = self.driver
        driver.get(self.website)

        rail_line_menu_button = driver.find_element_by_id('tool-line')
        rail_lines = driver.find_elements_by_class_name('rail-line')

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

    @unittest.skip(reason="GOOD")
    def test_paint_rail_line(self):

        """ Confirm that painting a rail line on the canvas stores that data in activeMap
        """

        driver = self.driver
        driver.get(self.website)

        rail_line_menu_button = driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        # Click the Red button
        rail_line_button = driver.find_element_by_id('rail-line-bd1038')
        rail_line_button.click()

        canvas = driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['17'],
            {'line': 'bd1038'},
        )

        # Click and drag
        # First, change the color (helps debugging)
        rail_line_button = driver.find_element_by_id('rail-line-0896d7')
        rail_line_button.click()
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 120, 100) # 20, 17
        action.click()
        action.click_and_hold()
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.move_by_offset(0, 5)
        action.release()
        action.perform()

        metro_map = driver.execute_script("return activeMap;")
        for col in range(17, 21): # 17, 18, 19, 20
            self.assertEqual(
                metro_map['20'][str(col)],
                {'line': '0896d7'}
            )

    @unittest.skip(reason="GOOD")
    def test_overpaint_rail_line(self):

        """ Confirm that painting over a coordinate with a different color will overwrite it
        """

        driver = self.driver
        driver.get(self.website)

        rail_line_menu_button = driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        # Click the Red button
        rail_line_button = driver.find_element_by_id('rail-line-bd1038')
        rail_line_button.click()

        canvas = driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['17'],
            {'line': 'bd1038'},
        )

        # Click the Blue button
        rail_line_button = driver.find_element_by_id('rail-line-0896d7')
        rail_line_button.click()

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['17'],
            {'line': '0896d7'},
        )

    @unittest.skip(reason='GOOD')
    def test_add_new_line(self):

        """ Confirm that adding a new rail line makes it available in the rail line options and in the global
        """

        driver = self.driver
        driver.get(self.website)

        rail_line_menu_button = driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        create_new_line_button = driver.find_element_by_id('rail-line-new')
        create_new_line_button.click()

        # I don't know the "correct" way to have Selenium actually click the color, so this will have to suffice
        driver.execute_script('document.getElementById("new-rail-line-color").value="#8efa00"')

        new_line_name = driver.find_element_by_id('new-rail-line-name')
        action = webdriver.common.action_chains.ActionChains(driver)
        action.send_keys_to_element(new_line_name, 'Lime Line')
        action.perform()
        save_new_line_button = driver.find_element_by_id('create-new-rail-line')
        save_new_line_button.click()

        # Confirm it actually will paint, too
        lime_line_button = driver.find_element_by_id('rail-line-8efa00')
        lime_line_button.click()

        # Click on the canvas at 100,100
        canvas = driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(driver) # Create a new action chains
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['17'],
            {'line': '8efa00'},
        )

        # Confirm it exists in the global
        self.assertEqual(
            metro_map['global']['lines']['8efa00'],
            {'displayName': 'Lime Line'}
        )

    @unittest.skip(reason='GOOD')
    def test_delete_unused_lines(self):

        """ Confirm that deleting unused lines only deletes the correct lines, and deletes them from the rail line options and the global
        """

        driver = self.driver
        driver.get(self.website)

        rail_line_menu_button = driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        self.helper_erase_blank_to_save(driver)
        metro_map = driver.execute_script("return activeMap;")

        # Of the defaults, only the purple line is not in use in the default WMATA map
        # Confirm it's there, then delete it
        self.assertEqual(
            metro_map['global']['lines']['662c90'],
            {'displayName': 'Purple Line'}
        )
        purple_line_button = driver.find_element_by_id('rail-line-662c90')

        delete_unused_lines_button = driver.find_element_by_id('rail-line-delete')
        delete_unused_lines_button.click()

        metro_map = driver.execute_script("return activeMap;")

        self.assertFalse(metro_map['global']['lines'].get('662c90'))
        with self.assertRaises(StaleElementReferenceException):
            purple_line_button.click()

        # Confirm the rest of the lines were not deleted
        remaining_lines = ["0896d7", "df8600", "000000", "00b251", "a2a2a2", "f0ce15", "bd1038", "79bde9", "cfe4a7"]
        for line in remaining_lines:
            self.assertTrue(metro_map['global']['lines'][line])
            line_button = driver.find_element_by_id(f'rail-line-{line}')

    @unittest.skip(reason='GOOD')
    def test_edit_line_colors(self):

        """ Confirm that editing an existing rail line's name and/or color works as intended, replacing all instances in the ui, global, and map data
        """

        driver = self.driver
        driver.get(self.website)

        # Wait 2 seconds for the default map to load; we're relying on Ft Totten to be there
        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        # Confirm Ft Totten exists before we change the red line's color
        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40'],
            {"line":"bd1038","station":{"transfer":1,"lines":["bd1038","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )

        # Count number of times the red line appears
        red_line_mentions = json.dumps(metro_map).count('bd1038')

        # Download the map as an image; after editing the color we'll make sure it's not the same
        download_as_image_button = driver.find_element_by_id('tool-export-canvas')
        download_as_image_button.click()
        map_image = driver.find_element_by_id('metro-map-image').get_attribute('src')
        download_as_image_button.click() # re-enable all the other buttons

        # Change the Red Line to the Lime Line
        rail_line_menu_button = driver.find_element_by_id('tool-line')
        rail_line_menu_button.click()

        edit_color_button = driver.find_element_by_id('rail-line-change')
        edit_color_button.click()

        edit_rail_line_select = Select(driver.find_element_by_id('tool-lines-to-change'))
        edit_rail_line_select.select_by_visible_text('Red Line')

        # I don't know the "correct" way to have Selenium actually click the color, so this will have to suffice
        driver.execute_script('document.getElementById("change-line-color").value="#8efa00"')

        edit_line_name = driver.find_element_by_id('change-line-name')
        edit_line_name.clear()
        action = webdriver.common.action_chains.ActionChains(driver)
        action.send_keys_to_element(edit_line_name, 'Lime Line')
        action.perform()

        save_rail_line_edits_button = driver.find_element_by_id('save-rail-line-edits')
        save_rail_line_edits_button.click()

        # Reload the map and confirm that everything is changed over
        metro_map = driver.execute_script("return activeMap;")
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
        download_as_image_button.click()
        new_map_image = driver.find_element_by_id('metro-map-image').get_attribute('src')
        download_as_image_button.click() # re-enable all the other buttons

        self.assertNotEqual(
            map_image,
            new_map_image
        )

    @unittest.skip(reason="GOOD")
    def test_add_station(self):

        """ Confirm that you can add a station to a coordinate with a rail line
        """

        driver = self.driver
        driver.get(self.website)

        station_button = driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = driver.find_element_by_id('metro-map-canvas')

        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 100, 330) # 17, 55
        action.click()
        # using .send_keys() also confirms that #station-name has been given focus
        action.send_keys('abc').send_keys(Keys.ENTER)
        action.perform()

        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['17']['55']['station']['name'],
            'abc'
        )

    @unittest.skip(reason='GOOD')
    def test_edit_station(self):

        """ Confirm that clicking on an existing station will edit it
        """

        driver = self.driver
        driver.get(self.website)

        station_button = driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = driver.find_element_by_id('metro-map-canvas')

        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40']['station']['name'],
            'Fort_Totten'
        )

        # Edit Ft Totten
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 562, 238) # 94, 40
        action.click()
        action.send_keys('abc').send_keys(Keys.ENTER)
        action.perform()

        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40']['station']['name'],
            'Fort_Tottenabc'
        )

    @unittest.skip(reason="GOOD")
    def test_noadd_empty_station(self):

        """ Confirm that clicking on a coordinate with a rail line to add a station, then clicking somewhere else will not create the station
        """

        driver = self.driver
        driver.get(self.website)

        station_button = driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 100, 323) # 17, 55
        action.click()
        action.perform()

        # Click to a different coordinate without saving the new station
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        metro_map = driver.execute_script("return activeMap;")
        self.assertFalse(
            metro_map['17']['55'].get('station')
        )

    @unittest.skip(reason="GOOD")
    def test_noadd_invalid_station_position(self):

        """ Confirm that a station cannot be placed on an empty coordinate
        """

        driver = self.driver
        driver.get(self.website)

        station_button = driver.find_element_by_id('tool-station')
        station_button.click()

        canvas = driver.find_element_by_id('metro-map-canvas')

        # Click on the canvas at 100,100
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = driver.execute_script("return activeMap;")
        self.assertFalse(metro_map['17'].get('17'))

    @unittest.skip("GOOD")
    def test_eraser(self):

        """ Confirm that erasing will delete any station and/or rail line at that coordinate
        """

        driver = self.driver
        driver.get(self.website)

        # Wait 2 seconds for the default map to load; we're relying on Ft Totten to be there
        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        # Confirm Ft Totten exists before we delete it
        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map['94']['40'],
            {"line":"bd1038","station":{"transfer":1,"lines":["bd1038","f0ce15","00b251"],"name":"Fort_Totten","orientation":"0"}}
        )

        eraser_button = driver.find_element_by_id('tool-eraser')
        eraser_button.click()

        canvas = driver.find_element_by_id('metro-map-canvas')

        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 562, 238) # 94, 40
        action.click()
        action.perform()

        metro_map = driver.execute_script("return activeMap;")
        self.assertFalse(
            metro_map['94'].get('40')
        )

    @unittest.skip(reason='GOOD')
    def test_download_as_image(self):

        """ Confirm that clicking download as image prepares the image canvas and disables the other buttons
        """

        driver = self.driver
        driver.get(self.website)

        # Wait 2 seconds for the default map to load; we're relying on the default WMATA map
        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        download_as_image_button = driver.find_element_by_id('tool-export-canvas')
        download_as_image_button.click()

        # Confirm that the button now reads "Edit Map"
        self.assertEqual(
            download_as_image_button.text,
            'Edit map'
        )

        # Confirm that the other buttons are disabled
        eraser_button = driver.find_element_by_id('tool-eraser')
        self.assertFalse(eraser_button.is_enabled())

        # Confirm that the src now has a data/img
        image_canvas = driver.find_element_by_id('metro-map-image')
        self.assertEqual(
            len(image_canvas.get_attribute('src')),
            1026214,
            "Has the default WMATA map been updated? Its length was last measured as 1026214"
        )

    @unittest.skip(reason='GOOD')
    def test_save_share_map(self):

        """ Confirm that clicking Save and Share map will generate a unique URL based on the mapdata, and visiting that URL contains a map with that data
        """

        driver = self.driver
        driver.get(self.website)

        self.helper_clear_draw_single_point(driver)

        # Download the map as an image for comparing later
        download_as_image_button = driver.find_element_by_id('tool-export-canvas')
        download_as_image_button.click()
        map_image = driver.find_element_by_id('metro-map-image').get_attribute('src')
        download_as_image_button.click() # re-enable all the other buttons

        save_map_button = driver.find_element_by_id('tool-save-map')
        save_map_button.click()

        WebDriverWait(driver, 1).until(
            expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
        )

        map_link = driver.find_element_by_id('shareable-map-link').get_attribute('href')
        metro_map = driver.execute_script("return activeMap;")

        driver.get(f'{map_link}')

        # Wait two seconds until the map has re-loaded
        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        self.helper_erase_blank_to_save(driver)
        new_metro_map = driver.execute_script("return activeMap;")

        self.assertEqual(metro_map, new_metro_map)

        download_as_image_button = driver.find_element_by_id('tool-export-canvas')
        download_as_image_button.click()
        new_map_image = driver.find_element_by_id('metro-map-image').get_attribute('src')
        download_as_image_button.click() # re-enable all the other buttons

        self.assertEqual(map_image, new_map_image)

    @unittest.skip(reason='GOOD')
    def test_save_share_map_no_overwrite(self):

        """ Confirm that clicking Save and Share map multiple times return the same urlhash
        """

        # Note: test_validation's test_valid_map_saves() also confirms
        #   that multiple posts with the same data do not overwrite
        #   the original mapdata or urlhash

        driver = self.driver
        driver.get(self.website)

        self.helper_clear_draw_single_point(driver)
        save_map_button = driver.find_element_by_id('tool-save-map')

        map_links = set()

        for attempt in range(5):
            save_map_button.click()

            WebDriverWait(driver, 2).until(
                expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
            )

            map_link = driver.find_element_by_id('shareable-map-link').get_attribute('href')
            map_links.add(map_link)

            # Prevent state elements by making sure we delete it in between saves
            driver.execute_script("document.getElementById('shareable-map-link').remove()")

        self.assertEqual(
            1,
            len(map_links)
        )

    @unittest.skip(reason='GOOD')
    def test_name_map(self):

        """ Confirm that a newly-created map can be named
        """

        # Note: Since Selenium tests use the browser, created maps go into the (production) database,
        #   NOT into the testing database.
        # As a result, I can't use SavedMap.objects.get() here after clicking #tool-save-map
        # But this is okay - I'm using test_validation's test_valid_map_saves() to confirm that the backend responds properly.

        driver = self.driver
        driver.get(self.website)

        self.helper_clear_draw_single_point(driver)
        save_button = driver.find_element_by_id('tool-save-map')
        save_button.click()
        
        WebDriverWait(driver, 1).until(
            expected_conditions.presence_of_element_located((By.ID, "shareable-map-link"))
        )

        map_link = driver.find_element_by_id('shareable-map-link')
        self.assertTrue(map_link.text)

        map_name = driver.find_element_by_id('user-given-map-name')
        action = webdriver.common.action_chains.ActionChains(driver)
        action.send_keys_to_element(map_name, 'single dot', Keys.ENTER)
        action.perform()

        name_map_button = driver.find_element_by_id('name-this-map')
        name_map_button.click()

        WebDriverWait(driver, 2).until(
            expected_conditions.invisibility_of_element((By.ID, 'name-this-map'))
        )

        self.assertEqual(
            'display: none;',
            name_map_button.get_attribute('style')
        )

    # def test_name_map_subsequent(self):

    #     """ Confirm that subsequent clicks to Save and Share map will remember what you named your previous map
    #     """

    # def test_name_map_no_overwrite(self):

    #     """ Confirm that a map that is named by an admin cannot be overwritten by a visitor
    #     """

    @unittest.skip(reason='GOOD')
    def test_show_hide_grid(self):

        """ Confirm that showing/hiding the grid works correctly
        """

        # Test by looking for the opacity change of the grid-canvas

        driver = self.driver
        driver.get(self.website)

        grid_button = driver.find_element_by_id('tool-grid')
        grid_canvas = driver.find_element_by_id('grid-canvas')

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

    @unittest.skip(reason='GOOD')
    def test_zoom_in(self):

        """ Confirm that zooming in resizes the canvas container and eventually shows the Snap to Left button
        """

        driver = self.driver
        driver.get(self.website)

        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        canvas_container = driver.find_element_by_id('canvas-container')
        columns = driver.execute_script("return gridCols;")
        width = int(canvas_container.value_of_css_property('width')[:-2])
        snap_controls_button = driver.find_element_by_id('snap-controls-left')

        zoom_in_button = driver.find_element_by_id('tool-zoom-in')
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

    @unittest.skip(reason='GOOD')
    def test_zoom_out(self):

        """ Confirm that zooming out resizes the canvas container
        """

        driver = self.driver
        driver.get(self.website)

        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        canvas_container = driver.find_element_by_id('canvas-container')
        columns = driver.execute_script("return gridCols;")
        width = int(canvas_container.value_of_css_property('width')[:-2])

        zoom_out_button = driver.find_element_by_id('tool-zoom-out')
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

    @unittest.skip(reason='GOOD')
    def test_snap_left_right(self):

        """ Confirm that the Snap Controls to Left/Right buttons correctly move the toolbox
        """

        driver = self.driver
        driver.get(self.website)

        WebDriverWait(driver, 2).until(
            expected_conditions.presence_of_element_located((By.ID, "rail-line-cfe4a7"))
        )

        canvas_container = driver.find_element_by_id('canvas-container')
        columns = driver.execute_script("return gridCols;")
        width = int(canvas_container.value_of_css_property('width')[:-2])
        snap_controls_left_button = driver.find_element_by_id('snap-controls-left')
        snap_controls_right_button = driver.find_element_by_id('snap-controls-right')

        zoom_in_button = driver.find_element_by_id('tool-zoom-in')
        zoom_in_button.click()
        zoom_in_button.click() # snap controls button appears in two zooms

        self.assertEqual(
            'block',
            snap_controls_left_button.value_of_css_property('display')
        )

        # Controls begins pinned to the right
        controls = driver.find_element_by_id('controls')
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

    @unittest.skip(reason='GOOD')
    def test_move_map(self):

        """ Confirm that using the "Move map" feature moves the painted rail lines and stations as expected
        """

        driver = self.driver
        driver.get(self.website)

        self.helper_clear_draw_single_point(driver)
        move_menu_button = driver.find_element_by_id('tool-move-all')
        move_menu_button.click()

        directions = ['up', 'down', 'left', 'right']

        move_buttons = {direction: driver.find_element_by_id(f'tool-move-{direction}') for direction in directions}

        # Initial state: 8,8
        metro_map = driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['8'])

        move_buttons['up'].click()
        metro_map = driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['7'])

        move_buttons['right'].click()
        metro_map = driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['9']['7'])

        move_buttons['down'].click()
        metro_map = driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['9']['8'])

        move_buttons['left'].click()
        metro_map = driver.execute_script('return activeMap;')
        self.assertTrue(metro_map['8']['8'])

        # Confirm that moving a point off the grid deletes it
        for click in range(1,9):
            move_buttons['left'].click()
            metro_map = driver.execute_script('return activeMap;')
            self.assertTrue(
                metro_map[str(8 - click)]['8']
            )
        else:
            move_buttons['left'].click()
            metro_map = driver.execute_script('return activeMap;')
            self.assertFalse(metro_map.get('0')) # 0,8 was the last coordinate

    # def test_resize_grid(self):

    #     """ Confirm that resizing the grid expands / contracts as expected; truncating the map data if necessary
    #     """

    @unittest.skip(reason="GOOD")
    def test_clear_map(self):

        """ Confirm that clicking Clear Map will delete all coordinate data
        """

        driver = self.driver
        driver.get(self.website)

        self.helper_erase_blank_to_save(driver)

        # Now activeMap has a value of the existing map
        metro_map = driver.execute_script("return activeMap;")
        self.assertTrue(type(metro_map) == dict, type(metro_map))
        self.assertTrue(len(metro_map) > 100) # default WMATA has ~140

        clear_map_button = driver.find_element_by_id('tool-clear-map')
        clear_map_button.click()

        metro_map = driver.execute_script("return activeMap;")
        self.assertTrue(type(metro_map) == dict, type(metro_map))
        self.assertTrue(len(metro_map) == 1)
        self.assertTrue(metro_map["global"]["lines"]) # Confirm that the lines still exist

    # def test_clear_delete_lines_refresh(self):

    #     """ Confirm that the default rail lines will be loaded when clearing map, then deleting the rail lines, then saving the map and reloading the page
    #     """
