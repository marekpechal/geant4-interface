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

def demo_geometry():
    geo = Geometry()
    geo.bodies.append(Body.box("sensor",
        (14, 14, 14), "G4_CESIUM_IODIDE", is_sensitive="sensor"))
    geo.bodies.append(Body.box("shield",
        (50, 50, 10), "G4_Fe", position=(0, 0, -100)))
    geo.bodies.append(Body.box("myworld",
        (250, 250, 250), "G4_AIR", is_world=True))
    return geo

def test_run_linux_cmd():
    result = run_linux_cmd("cd ~ && pwd")
    assert result == "/home/marek"

def test_run_g4iface_calls():
    geo = demo_geometry()
    run_g4iface(geo, macro=WSLFilename("init_headless.mac"))
    run_g4iface(str(geo), macro=HostFilename("init_headless.mac"))
    run_g4iface(WSLFilename("geometry.gdml"), macro=HostFilename("init_headless.mac"), run_ui=False)

if __name__ == "__main__":
    test_run_linux_cmd()
    test_run_g4iface_calls()
