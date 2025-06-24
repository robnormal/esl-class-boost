import os

class Environment:
    def __init__(self) -> None:
        pass

    def require(self, name: str, error_message: str = '') -> str:
        if name not in os.environ:
            msg = f"Environment variable {name} is not set"
            if error_message:
                msg += f": {error_message}"
            raise ValueError(msg)
        return os.environ.get(name)

    def is_prod(self):
        return self.require('ENVIRONMENT') == 'production'

environment = Environment()
