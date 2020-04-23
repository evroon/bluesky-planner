# BlueSky planner

Basic route planning plugin for [BlueSky](https://github.com/TUDelft-CNS-ATM/bluesky).
Part of the TU Delft AE4321-15 Air Traffic Management course.

## Goal
The goal of this plug-in is to create a route planner that calculates a route consisting of waypoints (fixes) that aircraft can follow to travel from their origin to the destination. These waypoints are placed close to the great circle between the origin and destination, resulting in a route that is almost as direct/short as the great circle itself.

## Usage
To use this program, first [BlueSky](https://github.com/TUDelft-CNS-ATM/bluesky) has to be downloaded and installed. After it has installed, put the `route.py` and `planner.py` files in the `plugins` directory of BlueSky. `planner.py` contains the code that actually represents the plug-in. route.py contains a class that does all the calculations in order to calculate the route and plot additional data, such as the grid or the great circle. The plug-in can be enabled by adding `'planner'` to `'enabled_plugins'` in the file `settings.cfg` in the root directory of BlueSky or by using the command `PLUGINS LOAD planner`.

Now the plugin can be used by entering the following command in BlueSky:

```
PLANNER [ACID] [ORIGIN] [DESTINATION]
```

This will create an aircraft, with acid as ID, flying from a certain origin to a certain destination. The parameters are optional, without them the aircraft (KL887) will follow a route from EHAM to VHHH on FL360 and with a speed of 300 knots. If the origin and destination are not valid ICAO codes for airports, an error message will be returned. Otherwise, it will output some data in the console of BlueSky. This includes a list of waypoints (the route), the length of the route and the length of the great circle (both in nautical miles).

Also, the plug-in will zoom and pan such that the route is visible. Finally, some radar settings are changed to make the route more clearly visible. If the plug-in is used multiple times after each other, the previously created aircraft will be deleted.

## Method
The plug-in creates a route by first determining which waypoints are close enough to the great circle to be considered. It does this by placing all waypoints in a grid. Subsequently, the grid cells that overlap with the great circle are determined. Also, their nearest neighbors are taken into account. Now, all the waypoints that are potentially part of the route are in these cells. For each cell, the waypoint that lies closest to the great circle is calculated. This is done analytically. However, some of the waypoints must be rejected. These waypoints are either too far off from the great circle or lie too close to (or even behind) another waypoint. Finally, a route is created by connecting all the waypoints that are left over.

## Limitations
There are some assumptions/limitations related to the plug-in. Most importantly:

* The plug-in calculates the most direct route, whereas this is rarely the case in reality.
* The plug-in doesn’t consider airways, only individual waypoints.
* The plug-in assumes a constant altitude and speed of the plane, although these can be changed in BlueSky by using additional commands (SPD and ALT for example). 
* The plug-in doesn’t support oceanic routes.
