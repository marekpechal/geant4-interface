import tempfile
import pyvista as pv

def plot_vrml_from_string(vrml_string):
    with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.wrl',
            delete=True,
            delete_on_close=False) as temp_file:

        temp_file.write(vrml_string)
        temp_file.close()

        plotter = pv.Plotter()
        plotter.import_vrml(temp_file.name)

    plotter.show_axes()
    plotter.isometric_view()
    plotter.show()
