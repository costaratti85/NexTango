class Settings:

    def __init__(self):

        self.pattern_type = ""
        self.pattern_name = ""
        self.input_file = ""

        self.step_x = 0.0
        self.step_y = 0.0

        self.hole_diameter = 0.0
        self.hole_distance = 0.0

        self.hole_shape = "circle"
        self.hole_size = 20.0

        self.margin = 0.0

        self.material = ""
        self.thickness = 0.0

        self.sheet_sizes = []

        self.output_file = ""

        self.cut_partial_figures = True