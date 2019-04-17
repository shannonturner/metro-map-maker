import unittest

from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from map_saver.models import SavedMap

class FrontendFunctionalityTestCase(TestCase):

    """ Selenium testing to confirm that front-end functionality changes do not cause regressions
    """

    website = 'http://127.0.0.1:8000/'

    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.close()

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

    def test_clear_map(self):

        """ Confirm that clicking Clear Map will delete all coordinate data
        """

        driver = self.driver
        driver.get(self.website)

        # activeMap begins as false until autoSaved, so erase a blank square to save
        eraser_button = driver.find_element_by_id('tool-eraser')
        canvas = driver.find_element_by_id('metro-map-canvas')
        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element_with_offset(canvas, 0, 0)
        action.click()
        action.perform()

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
        action.move_to_element_with_offset(canvas, 100, 100)
        action.click()
        action.perform()

        # Confirm that there is a line painted at the expected coordinates
        metro_map = driver.execute_script("return activeMap;")
        self.assertEqual(
            metro_map[17][17],
            {'line': 'bd1038'}
        )
