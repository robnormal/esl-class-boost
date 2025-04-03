import os

class Environment:
    def __init__(self) -> None:
        pass

    def require(self, name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise ValueError(f"Environment variable {name} is not set")
        return value

environment = Environment()