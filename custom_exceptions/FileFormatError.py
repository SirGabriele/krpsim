class FileFormatError(Exception):

    def __init__(self, line: str):
        self.message = (
            f"Line '{line}' does not respect file format:\n"
            f"- stock (n times): <name:quantity>\n"
            f"- process (n times): <name:(need1:qty1;need2:qty2;[...]):(result1:qty1;result2:qty2;[...]):delay>\n"
            f"- optimize (once): <optimize:(stock_name1|time;stock_name2|time;[...])>"
        )
        super().__init__(self.message)

    def __str__(self):
        return f"FileFormatError: {self.message}"
