def fail(error: str) -> dict:
    """
    Returns a dictionary indicating a failed operation with a provided error message.

    Args:
        error (str): The error message describing the reason for failure.

    Returns:
        dict: A dictionary containing 'status' set to False,
        a 'message' of 'fail', and the provided 'error' message.
    """
    return {
        'status': False,
        'message': 'fail',
        'error': error
    }
