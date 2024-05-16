from kedro.io import DataCatalog
from kedro.framework.context import KedroContext
from typing import Any  
import logging

logger = logging.getLogger(__name__)

def select_arg_by_type(args, arg_type, on_conflict='raise'):
    """
    Selects an argument of the specified type from the list of arguments.
    Handles conflicts based on the specified strategy.

    Args:
        args (list): List of arguments.
        arg_type (type): The type to search for in the arguments.
        on_conflict (str): Strategy to handle conflicts. Options are 'raise', 'first', 'last'.

    Returns:
        The argument of the specified type.

    Raises:
        ValueError: If there are multiple arguments of the specified type and on_conflict is 'raise'.
        TypeError: If no argument of the specified type is found.
    """
    selected_args = [arg for arg in args if isinstance(arg, arg_type)]

    if not selected_args:
     raise TypeError(f"No argument of type {arg_type.__name__} found.")

    if len(selected_args) > 1:
        if on_conflict == 'raise':
            raise ValueError(f"Multiple arguments of type {arg_type.__name__} found.")
        elif on_conflict == 'first':
            return selected_args[0]
        elif on_conflict == 'last':
            return selected_args[-1]
        else:
            raise ValueError(f"Invalid on_conflict value: {on_conflict}")

    return selected_args[0]


def get_mailer_param(args) -> dict[str, Any]:
    source = None
    for type in [KedroContext, DataCatalog]:
        try:
            source = select_arg_by_type(args, type, on_conflict="first")
            break
        except Exception:
            continue
    
    if source is None:
        raise TypeError("No KedroContext or DataCatalog found in arguments")

    if source.__class__.__name__ == "KedroContext":
        return source.params["error_mailer"]
    elif source.__class__.__name__ == "DataCatalog":
        return source.load("params:error_mailer")

def generate_error_info(parameters_source: (KedroContext|DataCatalog), hook_information: dict) -> dict:
    
    if parameters_source.__class__ == KedroContext:
        additional_info = parameters_source.params["error_mailer"]["additional_info"]
    elif parameters_source.__class__ == DataCatalog:
        additional_info = parameters_source.load("params:error_mailer.additional_info")
    else:
        raise TypeError("Invalid parameters source")

    extracted_params = {}
    for key, value in additional_info.items():
        extracted_params[key] = value
    
    extracted_params.update(hook_information)

    return extracted_params
