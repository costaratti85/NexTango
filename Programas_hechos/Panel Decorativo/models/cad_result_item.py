class CADResultItem:

    def __init__(
        self,
        name,
        quantity,
        material,
        thickness,
        geometry_items,
        occupied_width,
        occupied_height,
        cut_length_mm,
        pierce_count,
        bend_count=0,
    ):

        self.name = name

        self.quantity = quantity

        self.material = material
        self.thickness = thickness

        self.geometry_items = geometry_items

        self.occupied_width = occupied_width
        self.occupied_height = occupied_height

        self.cut_length_mm = cut_length_mm
        self.pierce_count = pierce_count
        self.bend_count = bend_count