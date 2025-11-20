class FileFormatStockError(Exception):

    STOCK_LINE_FORMAT = "name:quantity"

    def __init__(self, line: str):
        self.message = f"Line '{line}' does not respect format <{self.STOCK_LINE_FORMAT}>"
        super().__init__(self.message)

    def __str__(self):
        return f"FileFormatError: {self.message}"
