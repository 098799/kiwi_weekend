import unittest

import pytest

from . import main


class MainTests(unittest.TestCase):
    def setUp(self):
        self.bot = main.Bot()

    def test_locations_bcn(self):
        city_id = self.bot.get_id('Barcelona')
        self.assertEqual(city_id, '90595')

    def test_locations_madrid(self):
        city_id = self.bot.get_id('Madrid')
        self.assertEqual(city_id, '90155')

    @pytest.mark.integration
    def test_response(self):
        results = self.bot.scrape('Barcelona', 'Madrid', '2018-10-20')
        self.assertEqual(
            results[0],
            {
                'dep': '2018-10-20 01:00:00',
                'arr': '2018-10-20 08:35:00',
                'dst': 'Madrid - Barajas Airport T4',
                'src': 'Barcelona Estación Nord',
                'type': 'bus',
                'price': 32.71,
                'dst_id': 5555,
                'src_id': 595,
            }
        )
