from dataclasses import dataclass
import numpy as np

@dataclass
class Histogram1d:
    """
    Representation of a 1d histogram.

    Attributes
    ----------
    bins : np.ndarray
    underflow_count : int
    overflow_count : int
    """

    bins: np.ndarray = None
    underflow_count: int = 0
    overflow_count: int = 0

    @classmethod
    def from_xml(cls, root):
        """
        Load 1d histogram from a XML structure.

        Parameters
        ----------
        root : xml.etree.ElementTree.Element

        Returns
        -------
        histogram : Histogram1d
        """
        axis = root.find("axis")
        bins = np.zeros(int(axis.attrib["numberOfBins"]), dtype=int)
        underflow_count = 0
        overflow_count = 0
        for bin in root.find("data1d"):
            if bin.attrib["binNum"] == "UNDERFLOW":
                underflow_count = int(bin.attrib["entries"])
            elif bin.attrib["binNum"] == "OVERFLOW":
                overflow_count = int(bin.attrib["entries"])
            else:
                bins[int(bin.attrib["binNum"])] = int(bin.attrib["entries"])
        return cls(
            bins=bins,
            underflow_count=underflow_count,
            overflow_count=overflow_count,
            )
