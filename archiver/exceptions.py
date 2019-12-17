class ConfigException(Exception):
    pass


class FailureException(Exception):
    pass


class PathOutOfScopeException(Exception):
    """
    Raised to indicate a local path falls outside the current batch root.
    """
    def __init__(self, path, base_path):
        self.path = path
        self.base_path = base_path

    def __str__(self):
        return f'{self.path} is not contained within {self.base_path}'
