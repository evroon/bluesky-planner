""" BlueSky route planner plugin. """

from bluesky import stack, navdb
import numpy as np
from route import Route


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

    print(plan()[1])
    return config, stackfunctions


def update():
    pass


def preupdate():
    pass


def reset():
    pass


def plan(origin="EHAM", destination="VHHH"):
    route = Route(origin, destination)

    origin_index = np.where(np.array(navdb.aptid) == origin)
    destination_index = np.where(np.array(navdb.aptid) == destination)

    if len(origin_index) < 1:
        return False, 'Could not find origin'

    if len(destination_index) < 1:
        return False, 'Could not find destination'

    orig_lon, orig_lat = navdb.aptlon[origin_index][0], navdb.aptlat[origin_index][0]
    dest_lon, dest_lat = navdb.aptlon[destination_index][0], navdb.aptlat[destination_index][0]
    route.points = route.calculate_great_circle(orig_lon, orig_lat, dest_lon, dest_lat)

    point_count = len(route.points)
    middle = route.points[int(point_count / 2)]

    stack.stack('SWRAD APT')
    stack.stack('SWRAD VOR')
    stack.stack('ZOOM 0.02')
    stack.stack('PAN {},{}'.format(middle[1], middle[0]))

    route.calculate()
    route.plot_great_circle()
    route.plot_final_route()

    return True, 'Planned a route from {} to {}'.format(origin, destination)
