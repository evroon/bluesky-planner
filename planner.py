""" BlueSky route planner plugin. """
    
from bluesky import stack, navdb  #settings, traf, sim, scr, tools

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

def plan(origin="EHAM", destination="VHHH"):
    return True, 'Planning a route from {} to {}'.format(origin, destination)