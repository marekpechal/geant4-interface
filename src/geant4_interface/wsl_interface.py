from typing import Dict
import subprocess
import logging
import shutil, os, glob
import xml.etree.ElementTree as ET
from .data_analysis.histogram import Histogram1d
from .data_analysis.tracking import read_tracking_info
from .geometry import Geometry
logger = logging.getLogger(__name__)

WSL_ENV_NAME = "Geant4-Env"
WSL_G4IFACE_PATH = "/home/marek/geant4_workspace/Geant4_Interface/build/"
WSL_EXEC_NAME = "Geant4_Interface"

def wsl_linux_to_win_filename(wsl_linux_filename: str) -> str:
    """
    Convert path and filename in the WSL environemnt into the host Windows
    system's path and filename.

    Parameters
    ----------
    wsl_linux_filename : str

    Returns
    -------
    win_filename : str
    """

    return f"\\\\wsl.localhost\\{WSL_ENV_NAME}" \
        f"{wsl_linux_filename}".replace("/", "\\")

class WSLFilename(str):
    """Representation of a filename in the WSL environment."""

class HostFilename(str):
    """Representation of a filename in the host system."""

class ContentIn:
    """
    Context manager for passing content to the WSL environment.

    Takes content of type `Geometry`, `str`, `HostFilename` or
    `WSLFilename` or `None`.
      - if `Geometry`, the object is converted to string and written into a
        temporary file in the WSL environment
      - if `str`, the string is written into a temporary file
        in the WSL environment
      - if `HostFilename`, the file is copied to a temporary file in the
        WSL environment
      - if `WSLFilename`, nothing is done.
      - if `None`, nothing is done.

    Returns the name of the file in the WSL environment (to be used as
    argument to executables in the WSL environment) or `None` if `None` was
    passed in.

    The manager deletes any created temporary files on exit.

    Examples
    --------
    Pass file from host system to a command in the WSL environment.
    ```
    with ContentIn(HostFilename("file_on_host.mac")) as macro_filename:
        run_linux_cmd(f"do_something_with {macro_filename}")
    ```

    Pass file from WSL system to a command in the WSL environment.
    ```
    with ContentIn(WSLFilename("file_in_wsl.mac")) as macro_filename:
        run_linux_cmd(f"do_something_with {macro_filename}")
    ```

    Pass a string as a file to a command in the WSL environment.
    ```
    with ContentIn("file content as string...") as macro_filename:
        run_linux_cmd(f"do_something_with {macro_filename}")
    ```

    """

    def __init__(self, content, extension):
        self.content = content
        if isinstance(self.content, (WSLFilename, HostFilename)):
            if self.content.split(".")[-1] != extension:
                raise ValueError("incompatible extension")
        self.extension = extension
        self.to_delete = []

    def __enter__(self):
        if self.content is None:
            return
        if isinstance(self.content, WSLFilename):
            return self.content
        elif isinstance(self.content, (HostFilename, str, Geometry)):
            TMP_FILENAME = "tmp." + self.extension
            wsl_linux_filename = f"{WSL_G4IFACE_PATH}{TMP_FILENAME}"
            wsl_win_filename = wsl_linux_to_win_filename(wsl_linux_filename)
            if isinstance(self.content, HostFilename):
                logger.debug(f"copying {self.content} to {wsl_win_filename}")
                shutil.copy2(self.content, wsl_win_filename)
            else:
                with open(wsl_win_filename, "w") as f:
                    if isinstance(self.content, str):
                        f.write(self.content)
                    else:
                        f.write(str(self.content))
            self.to_delete.append(wsl_win_filename)
            return wsl_linux_filename
        else:
            raise ValueError(f"content of type {type(self.content)}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        for filename in self.to_delete:
            logger.debug(f"removing {filename}")
            os.remove(filename)

def run_linux_cmd(linux_cmd: str) -> None:
    """
    Run Linux command inside a WSL environment.

    Parameters
    ----------
    linux_cmd : str
    """

    win_command = [
        "wsl", "-d", WSL_ENV_NAME,
        "--", "bash", "-i", "-l", "-c",
        linux_cmd]
    logger.debug(f"running linux command: {linux_cmd}")

    result = subprocess.run(
        win_command,
        capture_output=True,
        text=True,
        check=True,
        )
    return result.stdout.strip()

def run_g4iface(
        geometry: str | HostFilename | WSLFilename,
        macro: str | HostFilename | WSLFilename = None,
        run_ui: bool = False,
        return_histogram: bool = False,
        return_tracking: bool = False,
        output_data_filename: str = None,
        return_vrml: bool = False,
        use_gps: bool = False,
        ) -> Dict[str, Histogram1d]:
    """
    Run the Geant4 interface.

    Parameters
    ----------
    geometry : str or HostFilename or WSLFilename
        Geometry to be loaded into the interface.
    macro : str or HostFilename or WSLFilename, optional
        Macro to be run in the interface. Defaults to None.
    run_ui : bool, optional
        Whether to run the graphical user interface. Defaults to False.
    return_histogram : bool, optional
        Whether to return histogram data. Defaults to False.
    return_tracking : bool, optional
        Whether to return tracking data. Defaults to False.
    output_data_filename : str, optional
        Name of the file into which to save output data.
    return_vrml : bool, optional
        Whether to return a VRML string. Defaults to False.
    use_gps : bool, optional
        Whether to use a general particle source. Defaults to False.

    Returns
    -------
    result : dict
        Dictionary with keys:
            "histograms" : Dict[str, Histogram1d]
                Histogram data. Present if `return_histogram` is True.
            "vrml" : str
                VRML representation of the geometry and simulated traces.
                Present if `return_vrml` is True.
    """

    logger.debug(
        f"running Geant4 interface ("
        f"run_ui={run_ui}, "
        f"return_histogram={return_histogram}, "
        f"output_data_filename={output_data_filename})")
    logger.debug(f"geometry passed as {type(geometry)}")
    logger.debug(f"macro passed as {type(macro)}")
    to_delete = []
    if (output_data_filename is None) and (return_histogram or return_tracking):
        output_data_filename = f"{WSL_G4IFACE_PATH}tmp.xml"
        to_delete.append(wsl_linux_to_win_filename(output_data_filename))
        to_delete.append(wsl_linux_to_win_filename(
            output_data_filename[:-4]+"_nt_StepData_t*.xml"))

    with ContentIn(macro, "mac") as macro_filename:
        with ContentIn(geometry, "gdml") as geometry_filename:
            linux_cmd = f"cd {WSL_G4IFACE_PATH} && "\
                f"./{WSL_EXEC_NAME} {geometry_filename}"
            if macro_filename is not None:
                linux_cmd += f" -m {macro_filename}"

            if run_ui:
                linux_cmd += " -i"
            if return_tracking:
                linux_cmd += " -t"
            if use_gps:
                linux_cmd += " -g"
            if output_data_filename is not None:
                linux_cmd += f" -o {output_data_filename}"
            run_linux_cmd(linux_cmd)

    result = {}

    if return_histogram:
        logger.debug(f"reading {output_data_filename}")
        result["histograms"] = {}
        with open(wsl_linux_to_win_filename(output_data_filename), "rb") as f:
            for root in ET.parse(f).getroot().findall("histogram1d"):
                result["histograms"][root.attrib["name"]] = \
                    Histogram1d.from_xml(root)

    if return_tracking:
        tracking_info = []
        for filename in glob.glob(wsl_linux_to_win_filename(
                output_data_filename[:-4]+"_nt_StepData_t*.xml")):
            logger.debug(f"reading {filename}")
            with open(filename, "rb") as f:
                tracking_info += read_tracking_info(ET.parse(f).getroot())
        result["tracking_info"] = sorted(tracking_info,
            key=lambda e: e.event_id)

    for filename in to_delete:
        for f in glob.glob(filename):
            logger.debug(f"removing {f}")
            os.remove(f)

    if return_vrml:
        filename = wsl_linux_to_win_filename(f"{WSL_G4IFACE_PATH}g4_00.wrl")
        if os.path.exists(filename):
            with open(filename, "r") as f:
                result["vrml"] = f.read()
            os.remove(filename)
        else:
            raise FileNotFoundError(f"no {filename} found; "
                "maybe macro does not initialize VRML2FILE?")

    return result
