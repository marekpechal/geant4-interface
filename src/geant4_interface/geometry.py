import xml.etree.ElementTree as ET

class Body:
    """
    Representation of a geometric body (building block of Geant4 geometry).

    Attributes
    ----------
    body_type : str
    name : str
    kwargs : dict
    position : np.ndarray
    is_sensitive : str or None
    is_world : bool
    material : str
    position_unit : str
    """
    def __init__(
            self,
            body_type: str,
            name: str,
            kwargs: dict,
            material: str,
            position: list = None,
            is_sensitive: str = None,
            is_world: bool = False,
            position_unit: str = "mm",
            ):

        if is_world and position is not None:
            raise ValueError("world cannot have an assigned position (?)")
        self.body_type = body_type
        self.name = name
        self.kwargs = kwargs
        self.position = position
        self.is_sensitive = is_sensitive
        self.is_world = is_world
        self.material = material
        self.position_unit = position_unit

    def to_xml_solid(self):
        """Convert the solid of the body to a XML element."""

        return ET.Element(
            self.body_type,
            name=self.name+"_solid",
            **{k: str(v) for k, v in self.kwargs.items()}
            )

    def to_xml_volume(self):
        """Convert the logical volume of the body to a XML element."""

        volume = ET.Element("volume",
            name="World" if self.is_world else self.name+"_log")
        ET.SubElement(volume, "materialref", ref=self.material)
        ET.SubElement(volume, "solidref", ref=self.name+"_solid")
        if self.is_sensitive is not None:
            ET.SubElement(volume, "auxiliary",
                auxtype="SensDet",
                auxvalue=self.is_sensitive
                )
        return volume

    def to_xml_physvol(self):
        """Convert the physical volume of the body to a XML element."""

        volume = ET.Element("physvol", name=self.name+"_phys")
        ET.SubElement(volume, "volumeref", ref=self.name+"_log")
        if self.position is not None:
            ET.SubElement(volume, "position",
                **{k: str(v) for k, v in zip("xyz", self.position)},
                unit=self.position_unit)
        return volume

    @classmethod
    def box(
            cls,
            name: str,
            size: list,
            material: str,
            **kwargs
            ):
        """
        Generate rectangular box body.
        """
        
        return cls("box", name, {k: v for k, v in zip("xyz", size)}, material,
            **kwargs)

class Geometry:
    """
    Representation of a Geant4 geometry.

    Attributes
    ----------
    bodies : List[Body]
    """

    def __init__(self):
        self.bodies = []

    def validate(self):
        """
        Check if geometry is valid.

        Raises
        ------
        ValueError : raised if geometry is not valid.
        """
        if sum(body.is_world for body in self.bodies) != 1:
            raise ValueError("exactly one body needs to be world")

    def to_xml(self) -> "xml.etree.ElementTree.Element":
        """Convert Geometry to XML element."""

        self.validate()
        gdml = ET.Element("gdml")
        solids = ET.SubElement(gdml, "solids")
        for body in self.bodies:
            solids.append(body.to_xml_solid())
        structure = ET.SubElement(gdml, "structure")
        for body in self.bodies:
            volume = body.to_xml_volume()
            if body.is_world:
                for body2 in self.bodies:
                    if body2 is body:
                        continue
                    volume.append(body2.to_xml_physvol())
            structure.append(volume)
        setup = ET.SubElement(gdml, "setup", name="Default", version="1.0")
        ET.SubElement(setup, "world", ref="World")
        return gdml

    def __str__(self):
        """Convert Geometry to XML string."""

        xml = self.to_xml()
        ET.indent(xml)
        return '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n'+\
            ET.tostring(xml).decode()
