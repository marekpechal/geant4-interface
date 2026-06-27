from geant4_interface.geometry import Geometry, Body
from geant4_interface.wsl_interface import run_g4iface
import matplotlib.pyplot as plt

if __name__ == "__main__":
    macro = \
        "/run/initialize\n" \
        "/gun/position 0 0 -1 cm\n" \
        "/gun/particle mu-\n" \
        "/gun/energy 6 GeV\n" \
        f"/run/beamOn 100000"

    geo = Geometry()
    geo.bodies.append(Body.box("sensor1",
        (14, 14, 14), "G4_CESIUM_IODIDE", is_sensitive="sensor1"))
    geo.bodies.append(Body.box("sensor2",
        (7, 7, 7), "G4_CESIUM_IODIDE", is_sensitive="sensor2",
        position=(0, 0, 50)))
    geo.bodies.append(Body.box("shield",
        (50, 50, 10), "G4_Fe", position=(0, 0, -100)))
    geo.bodies.append(Body.box("myworld",
        (250, 250, 250), "G4_AIR", is_world=True))

    result = run_g4iface(geo, macro=macro, return_histogram=True)

    plt.semilogy(result["histograms"]["sensor1"].bins)
    plt.semilogy(result["histograms"]["sensor2"].bins)
    plt.grid()
    plt.show()
