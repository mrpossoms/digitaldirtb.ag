from geography import Coordinate
from geography import Barrier
from trail import *


KEEP_OUT_ZONES = []


class Waypoint(LocationNode):
    def __init__(self, lat, lon, radius):
        self.lat = lat
        self.lon = lon
        self.radius = radius


class TripPlanner:
    def __init__(self):
        self.trails = TrailSet()
        self.barriers = [Barrier(Coordinate(45.108409, -86.2403), Coordinate(41.771532, -87.30887))]

    def route(self, start, destination):
        stop_chain = []

        self.trails.reset()

        start = self.trails.nearest(start, destination=start, use_last_score=False)
        start.last_score = start.score(waypoint=start, destination=destination)

        trails = []
        last = None

        while self.trails.all:
            u = self.trails.nearest(start, destination)
            u.visited = True

            if u.last_score == float('inf'):
                break

            self.trails.all.remove(u)

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