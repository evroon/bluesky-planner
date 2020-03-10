""" BlueSky route planner plugin. """

from bluesky import stack, navdb
import numpy as np
from route import Route

acid = ""


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
            'planner acid origin destination',

            # Cannot use acid as first parameter as aircraft doesn't exist yet.
            '[txt, txt, txt]',
            plan,
            'Create aircraft [acid] and plan a route from [origin] to [destination].']
    }

    return config, stackfunctions


def update():
    pass


def preupdate():
    pass


def reset():
    pass


def plan(p_acid="KL887", origin="EHAM", destination="VHHH"):
    '''Plan a route from origin to destination.'''
    global acid

    # If this is the first the function is called, set radar settings.
    # Otherwise, delete the previous aircraft and keep radar settings.
    if acid != '':
        stack.stack('DEL ' + acid)
    else:
        stack.stack('SWRAD APT')
        stack.stack('SWRAD VOR')
        stack.stack('SWRAD SAT')

    acid = p_acid
    route = Route(acid, origin, destination)

    origin_index = np.where(np.array(navdb.aptid) == origin)
    destination_index = np.where(np.array(navdb.aptid) == destination)

    if len(origin_index[0]) < 1:
        return False, 'Could not find origin'

    if len(destination_index[0]) < 1:
        return False, 'Could not find destination'

    orig_lon, orig_lat = navdb.aptlon[origin_index][0], navdb.aptlat[origin_index][0]
    dest_lon, dest_lat = navdb.aptlon[destination_index][0], navdb.aptlat[destination_index][0]
    route.points = route.calculate_great_circle(orig_lon, orig_lat, dest_lon, dest_lat)

    middle = route.points[int(len(route.points) / 2)]

    stack.stack('ZOOM 0.02')
    stack.stack('PAN {},{}'.format(middle[1], middle[0]))

    route.calculate()

    # Uncomment lines below to plot additional data.
    # route.plot_great_circle()
    # route.plot_active_grid()
    # route.plot_final_route()

    return True, 'Planned a route from {} to {}.'.format(origin, destination)
