class Whoops(Exception):
    def __init__(self, message: str, pass_on: str) -> None:
        super().__init__(f"{message} {pass_on}")
        self.message: str = message
        self.pass_on: str = pass_on
