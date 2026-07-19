from geant4_interface.wsl_interface import (
    run_linux_cmd,
    run_g4iface,
    WSLFilename,
    HostFilename,
    )
from geant4_interface.macros import (
    macro_template_gui_init,
    macro_template_VRML_init,
    )
from geant4_interface.utils import plot_vrml_from_string
from geant4_interface.geometry import Geometry, Body
import logging
import matplotlib.pyplot as plt
import numpy as np

def demo_geometry():
    geo = Geometry()
    geo.bodies.append(Body.box("sensor",
        (14, 14, 14), "G4_CESIUM_IODIDE", is_sensitive="sensor"))
    geo.bodies.append(Body.box("shield",
        (50, 50, 20), "G4_W", position=(0, 0, -50)))
    geo.bodies.append(Body.box("myworld",
        (250, 250, 250), "G4_AIR", is_world=True))
    return geo

macro = f"""
/run/initialize
/gun/position 2 0 -10 cm
/gun/particle mu+
/gun/energy 1.0 MeV
/run/beamOn 1000
"""

geo = demo_geometry()
result = run_g4iface(str(geo), macro=macro, run_ui=False, return_tracking=True)

interactions = {}

for event in result["tracking_info"]:
    print(f"EVENT {event.event_id}")
    print(event.info_str())

    for ia in event.interactions:
        ia_str = str(ia)
        interactions[ia_str] = interactions.get(ia_str, 0) + 1

print("LIST OF DISTINCT INTERACTIONS & NUMBERS OF THEIR OCCURRENCES:")
lst = sorted(interactions.items(), key=lambda p: -p[1])
for ia_str, count in lst:
    if count > 0.0005*lst[0][1]:
        print(f"{ia_str} ({count}x)")
print("...")
