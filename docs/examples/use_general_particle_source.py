from geant4_interface.macros import macro_template_gui_init
from geant4_interface.wsl_interface import run_g4iface
from geant4_interface.geometry import Geometry, Body
import matplotlib.pyplot as plt

if __name__ == "__main__":

    geo = Geometry()
    geo.bodies.append(Body.box("sensor",
        (14, 14, 14), "G4_W", is_sensitive="sensor"))
    geo.bodies.append(Body.box("myworld",
        (250, 250, 250), "G4_AIR", is_world=True))

    macro = \
        macro_template_gui_init + \
        "/run/initialize\n" \
        "/gps/pos/type Volume\n" \
        "/gps/pos/shape Para\n" \
        "/gps/pos/centre 0.0 0.0 -2.0 cm\n" \
        "/gps/pos/halfx 0.5 cm\n" \
        "/gps/pos/halfy 0.5 cm\n" \
        "/gps/pos/halfz 0.5 cm\n" \
        "/gps/ang/type iso\n" \
        "/gps/particle alpha\n" \
        "/gps/energy 5 MeV\n" \
        "/run/beamOn 100"
    run_g4iface(geo, macro=macro, run_ui=True, use_gps=True)

    macro = \
        "/run/initialize\n" \
        "/analysis/h1/set 0 400 0 10 MeV\n" \
        "/gps/pos/type Volume\n" \
        "/gps/pos/shape Para\n" \
        "/gps/pos/centre 0.0 0.0 -2.0 cm\n" \
        "/gps/pos/halfx 0.5 cm\n" \
        "/gps/pos/halfy 0.5 cm\n" \
        "/gps/pos/halfz 0.5 cm\n" \
        "/gps/ang/type iso\n" \
        "/gps/particle alpha\n" \
        "/gps/energy 5 MeV\n" \
        "/run/beamOn 100000"
    result = run_g4iface(geo, macro=macro, use_gps=True, return_histogram=True)

    plt.semilogy(result["histograms"]["sensor"].bins)
    plt.grid()
    plt.show()
