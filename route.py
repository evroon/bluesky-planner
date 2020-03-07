from bluesky import stack, navdb
import numpy as np
import collections
import pyproj
import csv


class Route:
    points = []
    speed = 300
    altitude = 'FL360'

    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination

    def calculate_great_circle(self, startlon, startlat, endlon, endlat, seperation=25):
        '''Calculate great circle from start to end
        Source: https://gis.stackexchange.com/questions/47/what-tools-in-python-are-available-for-doing-great-circle-distance-line-creati
        seperation is the distance between the points in km.
        '''

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
        '''Calculate route from origin to destination.'''
        self.active_grid = {}
        grid = self.create_grid()

        # Calculate grid cells that overlap with great circle.
        for p in self.points:
            self.active_grid[(np.floor(p[1]), np.floor(p[0]))] = True
            self.active_grid[(np.floor(p[1]), np.floor(p[0] - 1))] = True
            self.active_grid[(np.floor(p[1]), np.floor(p[0] + 1))] = True
            self.active_grid[(np.floor(p[1] - 1), np.floor(p[0]))] = True
            self.active_grid[(np.floor(p[1] + 1), np.floor(p[0]))] = True

        self.waypoints = []
        threshold = 1e4 # meters

        # Calculate closest waypoint to great circle for each cell.
        for k in self.active_grid.keys():
            if k in grid.keys():
                wpts = grid[k].split(',')
                dists = np.zeros(len(wpts))

                for i, w in enumerate(wpts):
                    wpt = int(w)
                    id = navdb.wpid[wpt]
                    lat = navdb.wplat[wpt]
                    lon = navdb.wplon[wpt]

                    # Ignore waypoints with ids that look like latitude values to avoid a bug in BlueSky.
                    if id[1:].isdigit():
                        dists[i] = 1e10
                    else:
                        dists[i] = np.absolute(cross_track_distance(self.startlat, self.startlon, self.endlat, self.endlon, lat, lon))

                closest = np.argmin(dists)

                # Ignore waypoints that are too far off.
                if (dists[closest] < threshold):
                    self.waypoints.append(int(wpts[closest]))

        # Remove waypoints that are not in the right direction.
        bearing_start = initial_bearing(self.startlat, self.startlon, self.endlat, self.endlon)
        bearing_end = (initial_bearing(self.endlat, self.endlon, self.startlat, self.startlon) - 180) % 360

        i, j = 0, -1
        for _ in range(5):
            bearing_first = initial_bearing(self.startlat, self.startlon, navdb.wplat[self.waypoints[i]], navdb.wplon[self.waypoints[i]])
            bearing_last = initial_bearing(navdb.wplat[self.waypoints[j]], navdb.wplon[self.waypoints[j]], self.endlat, self.endlon)

            if abs(bearing_first - bearing_start) > 30:
                del self.waypoints[i]
            else:
                i += 1

            if abs(bearing_last - bearing_end) > 30:
                del self.waypoints[j]
            else:
                j -= 1

        route = [navdb.wpid[x] for x in self.waypoints]
        print('Route is:', self.origin, ' '.join(route), self.destination)

        stack.stack('DEL,KL887')
        stack.stack('CRE,KL887,B772,{lat},{lon},182.55957037,300,450'.format(lat=self.startlat, lon=self.startlon))
        stack.stack('ORIG,KL887,{orig}'.format(orig=self.origin))
        stack.stack('DEST,KL887,{dest}'.format(dest=self.destination))

        for i, wpt in enumerate(route):
            lat = navdb.wplat[self.waypoints[i]]
            lon = navdb.wplon[self.waypoints[i]]
            stack.stack('MOVE,KL887,{lat},{lon}'.format(lat=lat, lon=lon))
            stack.stack('KL887 ADDWPT {wpt} {alt} {spd}'.format(wpt=wpt, alt=self.altitude, spd=self.speed))

        stack.stack('MOVE,KL887,{lat},{lon}'.format(lat=self.startlat, lon=self.startlon))
        self.calculate_route_length()


    def calculate_route_length(self):
        '''Calculate route and great circle length.'''
        route_length = 0
        great_circle_length = great_circle_distance__haversine(
            self.startlat, self.startlon,
            self.endlat, self.endlon
        )

        for i, _ in enumerate(self.waypoints[:-1]):
            route_length += great_circle_distance__haversine(
                navdb.wplat[self.waypoints[i]],   navdb.wplon[self.waypoints[i]],
                navdb.wplat[self.waypoints[i+1]], navdb.wplon[self.waypoints[i+1]]
            )

        # Add start and end legs.
        route_length += great_circle_distance__haversine(
            self.startlat, self.startlon,
            navdb.wplat[self.waypoints[0]], navdb.wplon[self.waypoints[0]]
        )
        route_length += great_circle_distance__haversine(
            navdb.wplat[self.waypoints[-1]], navdb.wplon[self.waypoints[-1]],
            self.endlat, self.endlon
        )

        print('Great circle length: {0:.0f}km'.format(great_circle_length / 1000))
        print('Calculated route length: {0:.0f}km'.format(route_length / 1000))
        print('Percentual increase in length: {0:.3f}%'.format((route_length / great_circle_length - 1) * 1e2))


    def plot_great_circle(self):
        '''Plot great circle path using lines.'''
        for i, _ in enumerate(self.points[:-1]):
            stack.stack('LINE ' + ','.join(['great_circle_point_' + str(i),
                                            str(self.points[i][1]),
                                            str(self.points[i][0]),
                                            str(self.points[i+1][1]),
                                            str(self.points[i+1][0])]
                                        ))


    def plot_final_route(self):
        '''Plot calculated route using lines.'''
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


    def plot_active_grid(self):
        '''Plot grid cells overlapping with great circle using boxes.'''
        for i, k in enumerate(self.active_grid.keys()):
            stack.stack('BOX ' + ','.join(['grid_' + str(i),
                                            str(k[0]),
                                            str(k[1]),
                                            str(k[0] + 1),
                                            str(k[1] + 1)]
                                        ))


    def create_grid(self):
        '''Calculate grid cells that overlap with great circle.'''
        grid = {}
        for i, _ in enumerate(navdb.wpid):
            lat = navdb.wplat[i]
            lon = navdb.wplon[i]
            key = (np.floor(lat), np.floor(lon))

            if key in grid:
                grid[key] += "," + str(i)
            else:
                grid[key] = str(i)

        return collections.OrderedDict(sorted(grid.items()))


# Source for all code below: https://github.com/FlightDataServices/FlightDataUtilities/blob/efda850fc9a4b77cae4fca65f4d02471098bc9c7/flightdatautilities/geometry.py
# Math is based on this: http://www.movable-type.co.uk/scripts/latlong.html
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
