from bluesky import stack, navdb
import numpy as np
import collections
import pyproj
import csv


class Route:
    points = []
    cache_path = 'output/grid_cache.csv'

    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination


    def calculate_great_circle(self, startlon, startlat, endlon, endlat, seperation=50):
        # Source: https://gis.stackexchange.com/questions/47/what-tools-in-python-are-available-for-doing-great-circle-distance-line-creati
        # seperation is the distance between the points in km.

        self.startlon = startlon
        self.startlat = startlat
        self.endlon = endlon
        self.endlat = endlat

        g = pyproj.Geod(ellps='WGS84')
        (_, _, dist) = g.inv(startlon, startlat, endlon, endlat)
        self.points = g.npts(startlon, startlat, endlon, endlat, 1 + int(dist / (seperation * 1000)))
        self.points.insert(0, (startlon, startlat))
        self.points.append((endlon, endlat))
        self.points = np.array(self.points)
        return self.points


    def calculate(self):
        active_grid = {}
        grid = self.create_cache()

        for p in self.points:
            active_grid[(np.floor(p[1]), np.floor(p[0]))] = True

        self.waypoints = []
        threshold = 1e4

        for k in active_grid.keys():
            if k in grid.keys():
                wpts = grid[k].split(',')
                dists = np.zeros(len(wpts))

                for i, w in enumerate(wpts):
                    wpt = int(w)
                    lat = navdb.wplat[wpt]
                    lon = navdb.wplon[wpt]
                    dists[i] = np.absolute(cross_track_distance(self.startlat, self.startlon, self.endlat, self.endlon, lat, lon))

                closest = np.argmin(dists)

                if (dists[closest] < threshold):
                    self.waypoints.append(int(wpts[closest]))


        route = [navdb.wpid[x] for x in self.waypoints]
        print(route)


    def plot_great_circle(self):
        for i, _ in enumerate(self.points[:-1]):
            stack.stack('LINE ' + ','.join(['great_circle_point_' + str(i),
                                            str(self.points[i][1]),
                                            str(self.points[i][0]),
                                            str(self.points[i+1][1]),
                                            str(self.points[i+1][0])]
                                        ))


    def plot_final_route(self):
        first_leg = ['route_first', self.startlat, self.startlon, navdb.wplat[self.waypoints[0]], navdb.wplon[self.waypoints[0]]]
        first_leg = [str(x) for x in first_leg]
        stack.stack('LINE ' + ','.join(first_leg))

        for i, _ in enumerate(self.waypoints[:-1]):
            stack.stack('LINE ' + ','.join(['route_' + str(i),
                                            str(navdb.wplat[self.waypoints[i]]),
                                            str(navdb.wplon[self.waypoints[i]]),
                                            str(navdb.wplat[self.waypoints[i+1]]),
                                            str(navdb.wplon[self.waypoints[i+1]])]
                                        ))

        last_leg = ['route_last', navdb.wplat[self.waypoints[-1]], navdb.wplon[self.waypoints[-1]], self.endlat, self.endlon]
        last_leg = [str(x) for x in last_leg]
        stack.stack('LINE ' + ','.join(last_leg))


    def create_cache(self):
        grid = {}
        for i, _ in enumerate(navdb.wpid):
            lat = navdb.wplat[i]
            lon = navdb.wplon[i]
            key = (np.floor(lat), np.floor(lon))

            if key in grid:
                grid[key] += "," + str(i)
            else:
                grid[key] = str(i)

        grid = collections.OrderedDict(sorted(grid.items()))
        return grid


# Source for all code below: https://github.com/FlightDataServices/FlightDataUtilities/blob/efda850fc9a4b77cae4fca65f4d02471098bc9c7/flightdatautilities/geometry.py
EARTH_RADIUS = 6371008  # volumetric mean radius (meters)

def cross_track_distance(p1_lat, p1_lon, p2_lat, p2_lon, p3_lat, p3_lon):
    d13 = great_circle_distance__haversine(p1_lat, p1_lon, p3_lat, p3_lon)
    b12 = np.radians(initial_bearing(p1_lat, p1_lon, p2_lat, p2_lon))
    b13 = np.radians(initial_bearing(p1_lat, p1_lon, p3_lat, p3_lon))
    return np.arcsin(np.sin(d13 / EARTH_RADIUS) * np.sin(b13 - b12)) * EARTH_RADIUS


def great_circle_distance__haversine(p1_lat, p1_lon, p2_lat, p2_lon):
    sdlat2 = np.sin(np.radians(p1_lat - p2_lat) / 2.) ** 2
    sdlon2 = np.sin(np.radians(p1_lon - p2_lon) / 2.) ** 2
    a = sdlat2 + sdlon2 * np.cos(np.radians(p1_lat)) * np.cos(np.radians(p2_lat))
    return 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)) * EARTH_RADIUS


def initial_bearing(p1_lat, p1_lon, p2_lat, p2_lon):
    dlon = np.radians(p2_lon - p1_lon)
    lat1 = np.radians(p1_lat)
    lat2 = np.radians(p2_lat)
    y = np.sin(dlon) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    return np.degrees(np.arctan2(y, x)) % 360
