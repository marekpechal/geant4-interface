import xml.etree.cElementTree as ET

class Body:
    def __init__(self, body_type, name, kwargs, material, position=None, is_sensitive=None, is_world=False, position_unit="mm"):
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
        return ET.Element(
            self.body_type,
            name=self.name+"_solid",
            **{k: str(v) for k, v in self.kwargs.items()}
            )

    def to_xml_volume(self):
        volume = ET.Element("volume",
            name="World" if self.is_world else self.name+"_log")
        ET.SubElement(volume, "materialref", ref=self.material)
        ET.SubElement(volume, "solidref", ref=self.name+"_solid")
        if self.is_sensitive is not None:
            ET.SubElement(volume, "auxiliary", auxtype="SensDet", auxvalue=self.is_sensitive)
        return volume

    def to_xml_physvol(self):
        volume = ET.Element("physvol", name=self.name+"_phys")
        ET.SubElement(volume, "volumeref", ref=self.name+"_log")
        if self.position is not None:
            ET.SubElement(volume, "position",
                **{k: str(v) for k, v in zip("xyz", self.position)},
                unit=self.position_unit)
        return volume

    @classmethod
    def box(cls, name, size, material, **kwargs):
        return cls("box", name, {k: v for k, v in zip("xyz", size)}, material,
            **kwargs)

class Geometry:
    def __init__(self):
        self.bodies = []

    def validate(self):
        if sum(body.is_world for body in self.bodies) != 1:
            raise ValueError("exactly one body needs to be world")

    def to_xml(self):
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
        xml = self.to_xml()
        ET.indent(xml)
        return '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n'+\
            ET.tostring(xml).decode()
