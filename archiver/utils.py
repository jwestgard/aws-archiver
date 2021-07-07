import re
from .exceptions import ConfigException, PathOutOfScopeException


def calculate_relative_path(batch_root, local_path):
    """
    Returns the relative path, i.e., the given local_path with the
    given batch_root prefix removed.

    :param batch_root: the path prefix to remove from the local path
    :param local_path: the local path to the file
    :return: the path relative to the batch_root
    :raises: PathOutOfScopeException if the given local_path does not match
             the given batch_root
    """
    if not batch_root.endswith('/'):
        batch_root += '/'

    batch_root_pattern = re.compile('(' + batch_root + ')')

    match = batch_root_pattern.match(local_path)
    if match:
        return local_path[len(match[1]):]
    else:
        raise PathOutOfScopeException(path=local_path, base_path=batch_root)
