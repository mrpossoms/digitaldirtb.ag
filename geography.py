import math

class Coordinate:
    def __init__(self, lat, lon):
        self.lat = float(lat)
        self.lon = float(lon)

    def point(self):
        u = math.pi * self.lon / 180.0
        v = math.pi * self.lat / 180.0
        eq_rad = 6378.1 # km
        eq_pol = 6356.8

        return [
            math.cos(u) * math.cos(v) * eq_rad,
            math.cos(u) * math.sin(v) * eq_rad,
            math.sin(u) * eq_pol
        ];

    def distance(self, coord):
        self.last_distance = math.sqrt(self.distance_square(coord))
        return self.last_distance

    def distance_square(self, coord):
        d_lon = self.lon - coord.lon
        d_lat = self.lat - coord.lat
        self.last_distance = d_lon * d_lon + d_lat * d_lat
        return self.last_distance

    def distance_euclidean(self, other):
        dist = 0
        p0 = self.point()
        p1 = other.point()
        for i in range(0, 3):
            dist += (p0[i] - p1[i]) ** 2
        self.last_distance = math.sqrt(dist)
        return self.last_distance

    def heading_to(self, waypoint):
        d_lat = waypoint.lat - self.lat
        d_lon = waypoint.lon - self.lon
        mag = math.sqrt(d_lat ** 2 + d_lon ** 2)

        if mag == 0:
            return None

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
        self.last_distance = float('inf')
