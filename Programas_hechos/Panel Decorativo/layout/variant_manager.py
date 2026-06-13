class VariantManager:

    def __init__(self, piece):

        self.piece = piece

        self.variants = {}

    def get_variant(self, classification):

        if classification in self.variants:

            print(
                f"REUTILIZANDO "
                f"{classification}"
            )

            return self.variants[
                classification
            ]

        print(
            f"GENERANDO "
            f"{classification}"
        )

        variant = self.create_variant(
            classification
        )

        self.variants[
            classification
        ] = variant

        return variant

    def create_variant(
        self,
        classification,
    ):

        #
        # TEMPORAL
        #
        # mas adelante:
        #
        # - clipping
        # - cierre
        # - reconstruccion
        #
        # por ahora devolvemos
        # la pieza original
        #

        return self.piece