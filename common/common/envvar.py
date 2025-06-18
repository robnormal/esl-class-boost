import os

class Environment:
    def __init__(self) -> None:
        pass

    def require(self, name: str, error_message: str = '') -> str:
        value = os.environ.get(name)
        if not value:
            msg = f"Environment variable {name} is not set"
            if error_message:
                msg += f": {error_message}"
            raise ValueError(msg)
        return value

environment = Environment()
