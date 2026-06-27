import subprocess
import logging
import shutil, os
import xml.etree.cElementTree as ET
from .data_analysis import Histogram
from .geometry import Geometry
logger = logging.getLogger(__name__)

WSL_ENV_NAME = "Geant4-Env"
WSL_G4IFACE_PATH = "/home/marek/geant4_workspace/Geant4_Interface/build/"
WSL_EXEC_NAME = "Geant4_Interface"

def wsl_linux_to_win_filename(wsl_linux_filename):
    return f"\\\\wsl.localhost\\{WSL_ENV_NAME}" \
        f"{wsl_linux_filename}".replace("/", "\\")

class WSLFilename(str):
    pass

class HostFilename(str):
    pass

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

def run_linux_cmd(linux_cmd):
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
        geometry,
        macro=None,
        run_ui=False,
        return_histogram=False,
        histogram_filename=None,
        return_vrml=False,
        use_gps=False,
        ):
    logger.debug(
        f"running Geant4 interface ("
        f"run_ui={run_ui}, "
        f"return_histogram={return_histogram}, "
        f"histogram_filename={histogram_filename})")
    logger.debug(f"geometry passed as {type(geometry)}")
    logger.debug(f"macro passed as {type(macro)}")
    to_delete = []
    if (histogram_filename is None) and return_histogram:
        histogram_filename = f"{WSL_G4IFACE_PATH}tmp.xml"
        to_delete.append(wsl_linux_to_win_filename(histogram_filename))

    with ContentIn(macro, "mac") as macro_filename:
        with ContentIn(geometry, "gdml") as geometry_filename:
            linux_cmd = f"cd {WSL_G4IFACE_PATH} && "\
                f"./{WSL_EXEC_NAME} {geometry_filename}"
            if macro_filename is not None:
                linux_cmd += f" -m {macro_filename}"

            if run_ui:
                linux_cmd += " -i"
            if use_gps:
                linux_cmd += " -g"
            if histogram_filename is not None:
                linux_cmd += f" -o {histogram_filename}"
            run_linux_cmd(linux_cmd)

    result = {}

    if return_histogram:
        logger.debug(f"reading {histogram_filename}")
        result["histograms"] = {}
        with open(wsl_linux_to_win_filename(histogram_filename), "rb") as f:
            for root in ET.parse(f).getroot().findall("histogram1d"):
                result["histograms"][root.attrib["name"]] = Histogram.from_xml(root)

    for filename in to_delete:
        logger.debug(f"removing {filename}")
        os.remove(filename)

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
