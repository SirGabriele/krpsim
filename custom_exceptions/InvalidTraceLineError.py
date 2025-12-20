class InvalidTraceLineError(Exception):

    def __init__(self, line: str):
        self.message = (
            f"Line '{line}' does not respect trace format:\n"
            f"- <cycle>:<process_name>"
        )
        super().__init__(self.message)

    def __str__(self):
        return f"InvalidTraceLineError: {self.message}"
