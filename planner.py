""" BlueSky route planner plugin. """

from bluesky import stack, navdb
import numpy as np
import pyproj


def init_plugin():
    config = {
        'plugin_name':     'planner',
        'plugin_type':     'sim',
        'update_interval': 2.5,
        'update':          update,
        'preupdate':       preupdate,
        'reset':           reset
    }

    stackfunctions = {
        'PLANNER': [
            'planner origin destination',
            '[txt, txt]',
            plan,
            'Plan a route from [origin] to [destination].']
    }

    return config, stackfunctions


def update():
    pass


def preupdate():
    pass


def reset():
    pass


def create_great_circle(startlon, startlat, endlong, endlat, seperation=100):
    # Source: https://gis.stackexchange.com/questions/47/what-tools-in-python-are-available-for-doing-great-circle-distance-line-creati
    # seperation is the distance between the points in km.

    g = pyproj.Geod(ellps='WGS84')
    (_, _, dist) = g.inv(startlon, startlat, endlong, endlat)
    lonlats = g.npts(startlon, startlat, endlong, endlat, 1 + int(dist / (seperation * 1000)))
    lonlats.insert(0, (startlon, startlat))
    lonlats.append((endlong, endlat))
    return lonlats


def plan(origin="EHAM", destination="VHHH"):
    origin_index = np.where(np.array(navdb.aptid) == origin)
    destination_index = np.where(np.array(navdb.aptid) == destination)

    if len(origin_index) < 1:
        return False, 'Could not find origin'

    if len(destination_index) < 1:
        return False, 'Could not find destination'

    origin_lon, origin_lat = navdb.aptlon[origin_index][0], navdb.aptlat[origin_index][0]
    destination_lon, destination_lat = navdb.aptlon[destination_index][0], navdb.aptlat[destination_index][0]
    points = create_great_circle(origin_lon, origin_lat, destination_lon, destination_lat)
    point_count = len(points)
    middle = int(point_count / 2)

    stack.stack('SWRAD APT')
    stack.stack('SWRAD VOR')
    stack.stack('ZOOM 0.04')
    stack.stack('PAN {},{}'.format(points[middle][1], points[middle][0]))

    lat_e = navdb.wplat -

    for i, _ in enumerate(points[:-1]):
        current = points[i]
        next = points[i+1]
        stack.stack('LINE ' + ','.join(['great_circle_point_' + str(i),
                                        str(current[1]),
                                        str(current[0]),
                                        str(next[1]),
                                        str(next[0])]
                                       ))

    return True, 'Planned a route from {} to {}'.format(origin, destination)
