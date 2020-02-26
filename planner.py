""" BlueSky route planner plugin. """
    
from bluesky import stack, navdb  #settings, traf, sim, scr, tools
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

# Source: https://gis.stackexchange.com/questions/47/what-tools-in-python-are-available-for-doing-great-circle-distance-line-creati
def create_great_circle(startlon, startlat, endlong, endlat):
    g = pyproj.Geod(ellps='WGS84')
    (az12, az21, dist) = g.inv(startlon, startlat, endlong, endlat)
    lonlats = g.npts(startlon, startlat, endlong, endlat, 1 + int(dist / 10000))

    # npts doesn't include start/end points, so prepend/append them
    # lonlats.insert(0, (startlon, startlat))
    # lonlats.append((endlong, endlat))
    return lonlats

def plan(origin="EHAM", destination="VHHH"):
    origin_index = np.where(np.array(navdb.aptid) == origin)
    destination_index = np.where(np.array(navdb.aptid) == destination)

    if len(origin_index) < 1:
        return False, 'Could not find origin'

    if len(destination_index) < 1:
        return False, 'Could not find destination'

    origin_lon, origin_lat = navdb.aptlon[origin_index], navdb.aptlat[origin_index]
    destination_lon, destination_lat = navdb.aptlon[destination_index], navdb.aptlat[destination_index]

    points = create_great_circle(origin_lon, origin_lat, destination_lon, destination_lat)

    for i, p in enumerate(points):
        stack.stack('CIRCLE ' + ','.join(['circle_point_' + str(i), str(p[1]), str(p[0]), '10']))

    return True, 'Planning a route from {} to {}'.format(origin, destination)
