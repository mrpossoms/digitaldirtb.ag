import math
import os
import http.client
import json
import time

SINGLETRACKS_API_KEY = '4LrZD8eibjmshtoAM8EcXm84NgiNp17UAvGjsnVAc43HXtGWcf'
KEEP_OUT_ZONES = []

class Coordinate:
    def __init__(self, lat, lon):
        self.lat = float(lat)
        self.lon = float(lon)

    def distance(self, coord):
        return math.sqrt(self.distance_square(coord))

    def distance_square(self, coord):
        d_lon = self.lon - coord.lon
        d_lat = self.lat - coord.lat
        return d_lon * d_lon + d_lat * d_lat

    def heading_to(self, waypoint):
        d_lat = waypoint.lat - self.lat
        d_lon = waypoint.lon - self.lon
        mag = math.sqrt(d_lat ** 2 + d_lon ** 2)

        return [d_lat / mag, d_lon / mag]

    def heading_coincidence(self, other, destination):
        other_heading = other.heading_to(destination)
        my_heading = self.heading_to(destination)

        coincidence = 0
        for i in range(len(other_heading)):
            coincidence += other_heading[i] * my_heading[i]

        c = (coincidence + 1) / 2
        assert 0 <= c <= 1

        return c

    def __str__(self):
        return '%f, %f' % (self.lat, self.lon)

    def __copy__(self):
        return Coordinate(self.lat, self.lon)

    def __sub__(self, other):
        return Coordinate(self.lat - other.lat, self.lon - other.lon)

    def __add__(self, other):
        return Coordinate(self.lat + other.lat, self.lon + other.lon)

    def __mul__(self, other):
        if other.__class__ == float:
            return Coordinate(self.lat * other, self.lon * other)
        elif other.__class__ == Coordinate:
            return Coordinate(self.lat * other.lat, self.lon * other.lon)

        return self

    def __rdiv__(self, other):
        if other.__class__ == float:
            return Coordinate(self.lat / other, self.lon / other)
        elif other.__class__ == Coordinate:
            return Coordinate(self.lat / other.lat, self.lon / other.lon)

        return self

    def __pow__(self, power, modulo=None):
        return Coordinate(self.lat ** 2, self.lon ** 2)

    def dot(self, other):
        return self.lat * other.lat + self.lon * other.lon

    def perpendicular(self):
        return Coordinate(self.lon, -self.lat)


class Barrier:
    def __init__(self, coord0, coord1):
        self.origin = coord0
        self.diagonal = coord1 - coord0
        self.normal = self.diagonal.perpendicular()

    def is_between(self, coord0, coord1):
        ray_direction = coord1 - coord0
        ray_origin = coord0 - self.origin

        t = -self.normal.dot(ray_origin) / (self.normal.dot(ray_direction))
        point = ray_origin + ray_direction * t

        # v0 * p + v1 * (1 - p) = point
        # v0 * p + v1 * -p * v1 = point

        # v0 - v1^2 = point / p
        # point / (v0 - v1^2) = p

        pv_lat = -point.lat / (self.origin.lat - (self.diagonal.lat))
        pv_lon = -point.lon / (self.origin.lon - (self.diagonal.lon))

        return 1 >= pv_lat >= 0 and 1 >= pv_lon >= 0


class LocationNode(Coordinate):
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.visited = False


class Waypoint(LocationNode):
    def __init__(self, lat, lon, radius):
        self.lat = lat
        self.lon = lon
        self.radius = radius


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

    def find_neighbors(self, trail_set):
        adj_path = self.path + '/' + self.filename + '.adj'
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

                for neighbor in neighbors:
                    if neighbor.trail_id != self.trail_id:
                        self.adjacent.append(neighbor)
                        fp.write(str(neighbor.trail_id) + '\n')
        else:
            with open(adj_path) as fp:
                for l in fp:
                    trail_id = int(l)
                    trail = trail_set.all[trail_id]
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
    def __init__(self, trails):
        self.all = trails

    def reset(self):
        for trail in self.all:
            trail.visited = False
            trail.last_score = math.inf
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

        for trail in self.all.values():
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

        if res.status != 200:
            print(res.readlines())
            time.sleep(1)
            continue

        lines = res.readlines()

        text = str(lines.pop(), 'utf8')
        json_obj = json.loads(text)['places']

        trails = []

        for place in json_obj:
            trails += [Trail(place)]

        return trails

    return  []

class TripPlanner:
    def __init__(self):
        self.all_trails = {}
        self.barriers = [Barrier(Coordinate(45.108409, -86.2403), Coordinate(41.771532, -87.30887))]

        if not os.path.exists('geo'):
            # m and M define a rectange that basically encapsulates the whole US
            m, M = Coordinate(48.061418, -125.551487), Coordinate(25.766589, -69.566654)

            total = (int(m.lat) - int(M.lat)) * (int(M.lon) - int(m.lon))
            processed = 0

            for lat in range(int(M.lat), int(m.lat)):
                for lon in range(int(m.lon), int(M.lon)):
                    processed += 1
                    print('%d/%d' % (total, processed))

                    for trail in trails_request(Coordinate(lat, lon), 80):
                        self.all_trails[trail.trail_id] = trail
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

                            self.all_trails[trail.trail_id] = trail

                        except json.decoder.JSONDecodeError:
                            print('fuck')

            trails = TrailSet(self.all_trails)

            trail_idx = 0
            for trail in self.all_trails.values():
                print(str(trail_idx) + '/' + str(len(self.all_trails)))
                trail.find_neighbors(trails)
                trail_idx += 1

    def route(self, start, destination):
        stop_chain = []

        ts = TrailSet(self.all_trails.values())
        ts.reset()

        start = ts.nearest(start, destination=start, use_last_score=False)
        start.last_score = start.score(waypoint=start, destination=destination)

        trails = []
        last = None

        while ts.all:
            u = ts.nearest(start, destination)
            u.visited = True

            if u.last_score == math.inf:
                break

            ts.all.remove(u)

            if destination.distance(u) < 0.1:
                last = u
                break

            for neighbor in u.adjacent:

                if neighbor is start or neighbor.visited is True: continue
                alt = u.last_score + neighbor.score(u, destination)

                if alt < neighbor.last_score:
                    neighbor.last_score = alt
                    neighbor.prev = u

            last = u

        while True:
            stop_chain = [last.as_dictionary] + stop_chain

            print(last)

            if not last.prev:
                break

            last = last.prev

        return stop_chain

    # while len(destinations) > 0:
    #     nearest = ts.nearest(last_coord, destinations[0], last_distance)[0]
    #     print("#%d %s" % (len(stop_chain), nearest))
    #     nearest.visited = True
    #     stop_chain.append(nearest.as_dictionary)
    #
    #     last_coord.lat = nearest.lat
    #     last_coord.lon = nearest.lon
    #
    #     if destinations[0].distance(last_coord) <= 1:
    #         print('-----------')
    #         destinations.pop()
    KEEP_OUT_ZONES.append(Barrier(Coordinate(41.666494, -87.237621), Coordinate(45.892313, -86.130711)))