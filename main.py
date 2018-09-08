import datetime
import json
import redis
import requests
import slugify


class Bot(object):
    def __init__(self, use_cache=True, local_redis=False):
        self.locations = None
        self.checkout_url = "https://www.alsa.com/en/web/bus/checkout"
        self.default_time = 3600

        self.session = requests.session()

        self.use_cache = use_cache
        self.local_redis = local_redis

        if self.use_cache:
            self.connect_redis()

    def connect_redis(self):
        redis_config = {'host': '35.198.72.72', 'port': 3389}
        local_config = {'host': 'localhost', 'port': 6379}

        if self.local_redis:
            redis_config = local_config

        self.redis = redis.StrictRedis(socket_connect_timeout=3, **redis_config)

    @property
    def cookie_params(self):
        return {
            'p_p_id': 'PurchasePortlet_WAR_Alsaportlet',
            'p_p_lifecycle': '1',
            'p_p_state': 'normal',
            '_PurchasePortlet_WAR_Alsaportlet_javax.portlet.action': 'searchJourneysAction',
            'originStationId': self.get_id(self.source),
            'destinationStationId': self.get_id(self.destination),
            'departureDate': self.date,
            '_departureDate': self.date,
        }

    def get_checkout_json(self):
        response = self.session.get(
            self.checkout_url,
            params=self.json_params,
            headers=self.json_headers,
        )
        return response.json()

    def get_cookies(self):
        if not self.session.cookies.get('JSESSIONID'):
            self.session.get(
                self.checkout_url,
                params=self.cookie_params
            )

    def get_id(self, name):
        redis_id = "city_id_{}".format(slugify.slugify(name))

        if self.use_cache:
            result = self.redis.get(redis_id)

            if result:
                result = result.decode("utf-8")

        else:
            result = ''

        if not result:
            self.get_locations()
            location = list(filter(lambda x: x['name'] == f'{name} (All stops)', self.locations))

            if not location:
                location = list(filter(lambda x: x['name'] == f'{name}', self.locations))

            if location:
                result = location[0].get('id')
                self.redis.setex(redis_id, self.default_time, result)

            return "90555"  # oopsie

        return result

    def get_locations(self):
        if not self.locations:
            with open('locations.json') as locations:
                self.locations = json.load(locations)

    @property
    def json_headers(self):
        return {'Cookie': 'JSESSIONID={}'.format(self.session.cookies.get('JSESSIONID'))}

    @property
    def json_params(self):
        return {
            'p_p_id': 'PurchasePortlet_WAR_Alsaportlet',
            'p_p_lifecycle': '2',
            'p_p_resource_id': 'JsonGetJourneysList',
            '_PurchasePortlet_WAR_Alsaportlet_journeyDirection': 'outward',
        }

    @staticmethod
    def output_date(previous_date):
        parsed_date = datetime.datetime.strptime(previous_date, "%d/%m/%Y %H:%M")
        return parsed_date.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def parse_date(date):
        year, month, day = date.split("-")
        return f"{month}/{day}/{year}"

    def parse_json(self, json_):
        results = []
        for journey in json_['journeys']:
            results.append(
                {
                    'dep': self.output_date(journey['departureDataToFilter']),
                    'arr': self.output_date(journey['arrivalDataToFilter']),
                    'dst': journey['destinationName'],
                    'src': journey['originName'],
                    'type': 'bus' if journey.get('busCharacteristic') else 'train',
                    'price': min(fare['price'] for fare in journey['fares']),
                    'dst_id': int(journey['destinationId']),
                    'src_id': int(journey['originId']),
                }
            )
        return results

    @staticmethod
    def previous_to_datetime(previous_date):
        return datetime.datetime.strptime(previous_date, "%m/%d/%Y")

    @staticmethod
    def redis_date(date_time_object):
        return date_time_object.strftime("%Y-%m-%d")

    def scrape(self, src, dst, date):
        """Main entry point."""
        self.source = src
        self.destination = dst
        self.date = self.parse_date(date)

        date = self.redis_date(self.previous_to_datetime(self.date))
        redis_id = "lol_journey_{}_{}_{}".format(self.get_id(self.source),
                                                 self.get_id(self.destination),
                                                 date)

        if self.use_cache:
            result = self.redis.get(redis_id)

            if result:
                result = json.loads(result.decode("utf-8"))

        if not isinstance(result, list) or not self.use_cache:
            result = ''

        if not result:
            self.get_cookies()
            json_ = self.get_checkout_json()
            result = self.parse_json(json_)

            if result:
                result = result
                self.redis.setex(redis_id, self.default_time, json.dumps(result))

        return result or None
