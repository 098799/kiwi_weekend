import datetime
import json
import requests


class Bot(object):
    def __init__(self, src, dst, date):
        self.source = src
        self.destination = dst
        self.date = self.parse_date(date)
        self.locations = None

        self.checkout_url = "https://www.alsa.com/en/web/bus/checkout"
        self.session = requests.session()

    @property
    def cookie_params(self):
        return {
            'p_auth': 'I3o78dGl',
            'p_p_id': 'PurchasePortlet_WAR_Alsaportlet',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_col_id': 'column-1',
            'p_p_col_count': '3',
            '_PurchasePortlet_WAR_Alsaportlet_javax.portlet.action': 'searchJourneysAction',
            'originStationId': self.get_id(self.source),
            'destinationStationId': self.get_id(self.destination),
            'departureDate': self.date,
            '_departureDate': self.date,
        }

    def do(self):
        """Main entry point."""
        self.get_cookies()
        json = self.get_checkout_json()

        return self.parse_json(json)

    def get_checkout_json(self):
        response = self.session.get(
            self.checkout_url,
            params=self.json_params,
            headers=self.json_headers,
        )
        return response.json()

    def get_cookies(self):
        self.session.get(self.checkout_url, params=self.cookie_params)

    def get_id(self, name):
        self.get_locations()
        location = list(filter(lambda x: x['name'] == f'{name} (All stops)', self.locations))
        return location[0].get('id')

    def get_locations(self):
        if not self.locations:
            with open('locations.json') as locations:
                self.locations = json.load(locations)

    @property
    def json_headers(self):
        return {
            'Cookie': 'JSESSIONID={}'.format(self.session.cookies.get('JSESSIONID')),
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML,'
                           'like Gecko) Chrome/68.0.3440.106 Safari/537.36'),
            }

    @property
    def json_params(self):
        return {
            'p_p_id': 'PurchasePortlet_WAR_Alsaportlet',
            'p_p_lifecycle': '2',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_resource_id': 'JsonGetJourneysList',
            'p_p_cacheability': 'cacheLevelPage',
            'p_p_col_id': 'column-1',
            'p_p_col_count': '1',
            '_PurchasePortlet_WAR_Alsaportlet_tabUuid': 'd077b7bb-5d13-4d98-a6a9-2036b8620c5d',
            '_PurchasePortlet_WAR_Alsaportlet_journeyDirection': 'outward',
            'tcontrol': '1536398024051',
        }

    @staticmethod
    def output_date(previous_date):
        parsed_date = datetime.datetime.strptime(previous_date, "%d/%m/%Y %H:%M")
        return parsed_date.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def parse_date(date):
        year, month, day = date.split("-")
        return f"{month}/{day}/{year}"

    def parse_json(self, json):
        results = []

        for journey in json['journeys']:
            results.append(
                {
                    'dep': self.output_date(journey['departureDataToFilter']),
                    'arr': self.output_date(journey['arrivalDataToFilter']),
                    'dst': journey['destinationName'],
                    'src': journey['originName'],
                    'type': 'bus' if journey.get('busCharacteristic') else 'train',
                    'price': journey['fares'][0]['price'],
                    'dst_id': journey['destinationId'],
                    'src_id': journey['originId'],
                }
            )

        return results
