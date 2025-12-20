class ProcessNameNotFoundError(Exception):

    def __init__(self, process_name: str):
        self.message = (
            f"The process '{process_name}' doesn\'t exists in the given input file."
        )
        super().__init__(self.message)

    def __str__(self):
        return f"ProcessNameNotFoundError: {self.message}"
