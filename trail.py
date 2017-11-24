from geography import LocationNode
from geography import Coordinate
import http.client
import json
import time
import os
import numpy as np

SINGLETRACKS_API_KEY = '4LrZD8eibjmshtoAM8EcXm84NgiNp17UAvGjsnVAc43HXtGWcf'
DIRECTIONS = []

class Trail(LocationNode):
    def __init__(self, dic):
        c = Coordinate(dic['lat'], dic['lon'])
        self.lat = c.lat
        self.lon = c.lon
        self.visited = False
        self.last_score = 0
        self.prev = None
        self.adjacent = []

        if 'unique_id' in dic:
            self.trail_id = dic['unique_id']

        if 'trail_id' in dic:
            self.trail_id = dic['trail_id']

        self.name = dic['name']
        self.description = dic['description']

        if 'rating' in dic:
            self.rating = dic['rating']

        if 'activities' in dic:
            self.rating = float(dic['activities'][0]['rating'])

        self.city = dic['city']
        self.state = dic['state']

    def find_neighbors(self, trail_set, adjacent=8):
        global DIRECTIONS

        adj_path = self.path + '/' + self.filename + '.adj'

        # pre compute direction vectors
        if len(DIRECTIONS) != adjacent:
            DIRECTIONS = []
            dt = 2 * np.pi / adjacent

            for t in range(0, adjacent):
                DIRECTIONS.append([np.cos(t * dt), np.sin(t * dt)])

        if not os.path.exists(adj_path):
            with open(adj_path, mode='w') as fp:
                radius = 1
                neighbors = []

                while True:
                    neighbors = trail_set.trails(at=self, within=radius)

                    if len(neighbors) < 10:
                        radius *= 2
                    else:
                        break

                def dist(item):
                    return item.last_distance

                neighbors = sorted(neighbors, key=dist)[:20]

                # TODO pickhttp://www.digitaldirtb.ag the neighbors that most closely point to the DIRECTIONS vector
                for dir in DIRECTIONS:
                    best_dot = 0
                    best = None
                    for neighbor in neighbors:
                        if neighbor is self: continue

                        heading = self.heading_to(neighbor)

                        if heading is None: continue

                        dot = -np.inner(heading, dir)

                        if best is None:
                            best = neighbor
                            best_dot = dot

                        if dot > best_dot and best not in self.adjacent:
                            best = neighbor
                            best_dot = dot

                    self.adjacent.append(best)
                    fp.write(str(best.trail_id) + '\n')

                # for neighbor in neighbors:
                #     if neighbor.trail_id != self.trail_id:
                #         self.adjacent.append(neighbor)
                #         fp.write(str(neighbor.trail_id) + '\n')
        else:
            with open(adj_path) as fp:
                for l in fp:
                    trail_id = int(l)
                    trail = trail_set.all_table[trail_id]
                    self.adjacent.append(trail)

    def score(self, waypoint, destination):

        distance_to_destination = self.distance_square(destination)
        distance_from_traveler = self.distance_square(waypoint)

        if distance_to_destination == 0 or distance_from_traveler == 0:
            return 0

        # Prevent the algorithm from crossing undesired boundaries
        # for keepout in KEEP_OUT_ZONES:
        #     if keepout.is_between(self, waypoint):
        #         return math.inf

        return distance_to_destination / (self.rating + 1) ** 3

        # lots of meandering, but ignores trails that are good and nearby
        #return (distance_to_destination * 0.02 + distance_from_traveler * 2) - self.rating

    @property
    def as_dictionary(self):
        return {
            'lat': self.lat,
            'lon': self.lon,
            'trail_id': self.trail_id,
            'name': self.name,
            'description': self.description,
            'rating': self.rating,
            'city': self.city,
            'state': self.state}

    @property
    def path(self):
        return "geo/%d_%d" % (int(self.lat), int(self.lon))

    @property
    def filename(self):
        return "%d-%f" % (self.trail_id, self.rating)

    def store(self):
        path = self.path
        if not os.path.exists(path):
            os.makedirs(path)

        with open(os.path.join(path, self.filename), 'w') as fd:
            fd.write(json.dumps(self.as_dictionary))

    def __str__(self):
        return "(%f) %s - %s @ %f,%f" % (self.rating, self.name, self.state, self.lat, self.lon)

    def __lt__(self, other):
        return self.last_score > other.last_score

    def __eq__(self, other):
        return self.last_score == other.last_score


class TrailSet:
    def __init__(self):
        self.all = []
        self.all_table = {}

        if not os.path.exists('geo'):
            # m and M define a rectange that basically encapsulates the whole US
            m, M = Coordinate(48.061418, -125.551487), Coordinate(25.766589, -69.566654)

            step = 0.25
            d_lat = (m.lat - M.lat) / 0.25
            d_lon = (M.lon - m.lon) / 0.25
            total = d_lat * d_lon
            processed = 0

            for lat in np.arange(int(M.lat), int(m.lat), step):
                for lon in np.arange(int(m.lon), int(M.lon), step):
                    processed += 1
                    print('%d/%d' % (total, processed))

                    miles_radius = Coordinate(lat, lon).distance_euclidean(Coordinate(lat + step, lon + step)) * 1.6

                    for trail in trails_request(Coordinate(lat, lon), miles_radius):
                        self.all.append(trail)
                        self.all_table[trail.trail_id] = trail
                        trail.store()
        else:
            for path in os.listdir('geo'):
                if os.path.isfile(path):
                    continue

                path = os.path.join('geo', path)
                for file in os.listdir(path):
                    if '.adj' in file:
                        continue

                    with open(os.path.join(path, file)) as fd:
                        try:
                            dic = json.load(fp=fd)
                            trail = Trail(dic)

                            self.all_table[trail.trail_id] = trail

                        except json.decoder.JSONDecodeError:
                            print('fuck')

        trail_idx = 0
        total = len(self.all_table.values())
        for trail in self.all_table.values():
            print('%d/%d' % (trail_idx, total))
            trail.find_neighbors(self)
            trail_idx += 1

    def reset(self):
        self.all = []

        for trail in self.all_table.values():
            self.all.append(trail)
            trail.visited = False
            trail.last_score = float("inf")
            trail.last_distance = float('inf')
            trail.prev = None

    def nearest(self, coord, destination, use_last_score=True):
        def score(item):
            if use_last_score:
                return item.last_score
            else:
                return item.score(coord, destination)

        self.all = sorted(self.all, key=score)

        return self.all[:1][0]

    def trails(self, at, within=0.1):
        trails = []

        for trail in self.all_table.values():
            if trail is at: continue
            if trail.distance_square(at) < within ** 2:
                trails.append(trail)

        return trails


def trails_request(coord, radius=25, limit=4000):
    headers = {
        'X-Mashape-Key': SINGLETRACKS_API_KEY,
        'Accept': 'text/plain',
    }

    for _ in range(1, 3):
        con = http.client.HTTPSConnection('trailapi-trailapi.p.mashape.com')
        query = '/?lat=%f&lon=%f&radius=%f&limit=%d&q[activities_activity_type_name_eq]=mountain+biking' % (
        coord.lat, coord.lon, radius, limit)
        con.request('GET', query, headers=headers)

        res = con.getresponse()
        text = res.read()

        if res.status != 200:
            print(text)
            time.sleep(1)
            continue

        if isinstance(text, bytes):
            text = text.decode('utf8')

        json_obj = json.loads(text)['places']

        trails = []

        for place in json_obj:
            trails += [Trail(place)]

        return trails

    return []
