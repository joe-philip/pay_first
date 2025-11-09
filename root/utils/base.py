from typing import Any


def fail(error: str, **kwargs) -> dict:
    """
    Returns a dictionary indicating a failed operation
    with a provided error message.

    Args:
        error (str): The error message describing the reason for failure.

    Returns:
        dict: A dictionary containing 'status' set to False,
        a 'message' of 'fail', and the provided 'error' message.
    """
    return {
        'status': False,
        'message': 'fail',
        'error': error,
        **kwargs
    }


def success(data: Any) -> dict:
    """
    Returns a standardized success response dictionary.

    Args:
        data (Any): The data to include in the response.

    Returns:
        dict: A dictionary containing the status, message,
        and provided data under the 'data' key.
    """
    return {
        'status': True,
        'message': 'success',
        'data': data
    }
