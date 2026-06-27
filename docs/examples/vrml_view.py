from geant4_interface.macros import macro_template_VRML_init
from geant4_interface.utils import plot_vrml_from_string
from geant4_interface.geometry import Geometry, Body
from geant4_interface.wsl_interface import run_g4iface

if __name__ == "__main__":
    macro = \
        macro_template_VRML_init + \
        "/run/initialize\n" \
        "/gun/position 0 0 -11 cm\n" \
        "/gun/particle mu-\n" \
        "/gun/energy 6 GeV\n" \
        "/run/beamOn 100\n" \

    geo = Geometry()
    geo.bodies.append(Body.box("sensor",
        (14, 14, 14), "G4_CESIUM_IODIDE", is_sensitive="sensor"))
    geo.bodies.append(Body.box("shield",
        (50, 50, 10), "G4_Fe", position=(0, 0, -100)))
    geo.bodies.append(Body.box("myworld",
        (250, 250, 250), "G4_AIR", is_world=True))

    result = run_g4iface(geo, macro=macro, return_vrml=True)
    plot_vrml_from_string(result["vrml"])
