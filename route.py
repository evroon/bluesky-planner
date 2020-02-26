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

    def calculate_great_circle(self, startlon, startlat, endlon, endlat, seperation=100):
        # Source: https://gis.stackexchange.com/questions/47/what-tools-in-python-are-available-for-doing-great-circle-distance-line-creati
        # seperation is the distance between the points in km.

        self.startlon = startlon
        self.startlat = startlat
        self.endlon = endlon
        self.endlat = endlat

        g = pyproj.Geod(ellps='WGS84')
        (_, _, dist) = g.inv(startlon, startlat, endlon, endlat)
        self.points = g.npts(startlon, startlat, endlon,
                             endlat, 1 + int(dist / (seperation * 1000)))
        self.points.insert(0, (startlon, startlat))
        self.points.append((endlon, endlat))
        self.points = np.array(self.points)
        return self.points

    def calculate(self):
        active_grid = {}
        grid = self.create_cache()

        for p in self.points:
            active_grid[(np.floor(p[1]), np.floor(p[0]))] = True

        # try:
        #     cache = np.genfromtxt(cache_path, delimiter=';')
        # except OSError:
        #     create_cache()
        #     cache = np.genfromtxt(cache_path, delimiter=';')

        self.waypoints = []

        for k in active_grid.keys():
            if k in grid.keys():
                wpts = grid[k].split(',')
                if len(wpts) == 1:
                    self.waypoints.append(int(wpts[0]))

    def plot_great_circle(self):
        for i, _ in enumerate(self.points[:-1]):
            stack.stack('LINE ' + ','.join(['great_circle_point_' + str(i),
                                            str(self.points[i][1]),
                                            str(self.points[i][0]),
                                            str(self.points[i+1][1]),
                                            str(self.points[i+1][0])]
                                           ))

    def plot_final_route(self):
        first_leg = ['route_first', self.startlat, self.startlon,
                     navdb.wplat[self.waypoints[0]], navdb.wplon[self.waypoints[0]]]
        first_leg = [str(x) for x in first_leg]
        stack.stack('LINE ' + ','.join(first_leg))

        for i, _ in enumerate(self.waypoints[:-1]):
            stack.stack('LINE ' + ','.join(['route_' + str(i),
                                            str(navdb.wplat[self.waypoints[i]]),
                                            str(navdb.wplon[self.waypoints[i]]),
                                            str(navdb.wplat[self.waypoints[i+1]]),
                                            str(navdb.wplon[self.waypoints[i+1]])]
                                           ))

        last_leg = ['route_last', navdb.wplat[self.waypoints[-1]],
                    navdb.wplon[self.waypoints[-1]], self.endlat, self.endlon]
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

        # output = ""
        # for k, v in grid.items():
        #     output += str(k[0]) + ';' + str(k[1]) + ';' + v + "\n"

        # f = open(cache_path, 'w')
        # f.write(output)
        # f.close()
