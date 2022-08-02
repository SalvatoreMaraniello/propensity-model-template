"""Provides support to read/manipulate yaml files"""

import pathlib
import enum
import yaml
from typing import Optional, Union, List, Tuple


class FILEextension(enum.Enum):
    """Defines (valid) YAML file extensions"""
    YAMLext = 'yml', 'yaml'
    OTHERext = None

    @classmethod
    def _missing_(cls, file_name_or_extension: str):
        """
        This method allows:
        - mapping YAMLext to multiple extentions
        - passing full path to file as input
        """
        if (file_name_or_extension in cls.YAMLext.value or
                pathlib.Path(file_name_or_extension).suffix[1:] in cls.YAMLext.value):
            return cls(cls.YAMLext.value)
        return cls(None)


class YamlIOException(Exception):
    """ Class for handling exceptions during input/output operations with YAML files"""

    def __init__(self, msg: str) -> None:
        """ Allow custom error message """
        self.msg = msg

    def __repr__(self) -> str:
        """Returns the custom error message"""
        return self.msg


def read_yaml(path_to_file: str) -> dict:
    """
    Reads content of yaml file into dictionary. 
    An error is raised if file extension is not recognised.
    """

    if FILEextension(path_to_file) == FILEextension.YAMLext:
        return yaml.safe_load(open(path_to_file, 'r'))
    raise YamlIOException(f'{path_to_file} is not a YAML')


def read_yaml_from_dir(
    path_to_dir: str,
    on_error_continue: Optional[bool] = False,
    max_depth: Optional[int] = 3
) -> Union[dict, Tuple[dict, List[str]]]:
    """Load all (and only) YAML files in folder, including nested directories up to a specified depth.

    Args:
        path_to_dir (str): Path to folder/yaml file
        on_error_continue (Optional[bool], optional): If True, it will not raise error if a file with 
            yaml extension fails to load. Defaults to False.
        max_depth (Optional[int], optional): List of (yaml) file names which failed loading. Only 
            returned if `on_error_continue=True`. Defaults to 3.

    Raises:
        FILEextension error. 

    Returns:
        collection (dict): dictionary with (possibly nested) dictionaries.
        failed_yaml (list of str): name of files which could not be loaded.
    """

    # if path_to_dir is a directory, loop through its items
    collection, failed_yaml = {}, []

    for file_or_dir in pathlib.Path(path_to_dir).iterdir():
        f_path = str(file_or_dir.absolute())

        # if sub-directory: read only if maximum depth not reached
        if file_or_dir.is_dir() and max_depth > 0:
            new_item, failed_here = read_yaml_from_dir(
                f_path, on_error_continue,  max_depth-1)
            failed_yaml += failed_here

        # if YAML, try to read
        elif FILEextension(f_path) == FILEextension.YAMLext:
            try:
                new_item = read_yaml(f_path)
            except Exception as err:
                if on_error_continue:
                    failed_yaml.append(f_path)
                    continue
                raise err

        # else ignore file
        else:
            continue

        # If sub-directory/file contain something, store
        if bool(new_item):
            collection[file_or_dir.stem] = new_item

    return collection, failed_yaml


if __name__ == "__main__":
    coll, failed = read_yaml_from_dir('./schemas', False, 2)
