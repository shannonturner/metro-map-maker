import unittest

from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

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
        action.move_to_element_with_offset(canvas, 100, 100) # 17, 17
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

    # def test_subsequent_loads_saved_map(self):
    #     """ Confirms that subsequent page loads will load the map saved in localstorage rather than the default WMATA map
    #     """

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

    @unittest.skip(reason="TODO: needs work on click+drag")
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

        # TODO: Click and drag (needs work)
        # Click and drag
        # First, change the color (helps debugging)
        # rail_line_button = driver.find_element_by_id('rail-line-0896d7')
        # rail_line_button.click()
        # action = webdriver.common.action_chains.ActionChains(driver)
        # action.move_to_element_with_offset(canvas, 120, 100) # 20, 17
        # action.click_and_hold()
        # action.move_by_offset(0, 20)
        # action.release()
        # # # action.move_to_element_with_offset(canvas, 120, 120) # 20, 20
        # # action.drag_and_drop_by_offset(canvas, 120, 120)
        # action.perform()

        # import pdb; pdb.set_trace()

        # metro_map = driver.execute_script("return activeMap;")
        # for col in range(17, 21): # 17, 18, 19, 20
        #     self.assertEqual(
        #         metro_map['20'][str(col)],
        #         {'line': '0896d7'}
        #     )

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

    # def test_add_new_line(self):

    #     """ Confirm that adding a new rail line makes it available in the rail line options and in the global
    #     """

    # def test_delete_unused_lines(self):

    #     """ Confirm that deleting unused lines only deletes the correct lines, and deletes them from the rail line options and the global
    #     """

    # def test_edit_line_colors(self):

    #     """ Confirm that editing an existing rail line's name and/or color works as intended, replacing all instances in the ui, global, and map data
    #     """

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

    # def test_save_share_map(self):

    #     """ Confirm that clicking Save and Share map will generate a unique URL based on the mapdata, and visiting that URL contains a map with that data
    #     """

    # def test_save_share_map_no_overwrite(self):

    #     """ Confirm that clicking Save and Share map multiple times return the same urlhash
    #     """

    #     # Note: test_validation's test_valid_map_saves() also confirms
    #     #   that multiple posts with the same data do not overwrite
    #     #   the original mapdata or urlhash

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

    # def test_move_map(self):

    #     """ Confirm that using the "Move map" feature moves the painted rail lines and stations as expected
    #     """

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

