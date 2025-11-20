class FileFormatOrderError(Exception):

    def __init__(self):
        self.message = f"File does not respect format order: stock > process > optimize."
        super().__init__(self.message)

    def __str__(self):
        return f"FileFormatError: {self.message}"
