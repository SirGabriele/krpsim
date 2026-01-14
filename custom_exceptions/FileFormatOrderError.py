class FileFormatOrderError(Exception):

    def __init__(self):
        self.message = "File does not respect format order: stock > process > optimize."
        super().__init__(self.message)

    def __str__(self):
        return f"FileFormatOrderError: {self.message}"
