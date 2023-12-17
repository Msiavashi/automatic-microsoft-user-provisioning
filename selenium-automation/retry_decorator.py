import functools
import logging
import time

from microsoft_credential_manager import MicrosoftAccessPassValidationException


def retry(exceptions, tries=3, delay=5, backoff=2):
    """
    Decorator for retrying a function if exception occurs.

    :param exceptions: Exceptions that trigger a retry
    :param tries: Number of tries to attempt
    :param delay: Initial delay between retries in seconds
    :param backoff: Backoff multiplier e.g. value of 2 will double the delay each retry
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs, retries_exhausted=False)
                except exceptions as e:
                    if isinstance(e, MicrosoftAccessPassValidationException):
                        mtries += 2
                    msg = f"Retrying in {mdelay} seconds..."
                    logging.info(msg)  # or use logging
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs, retries_exhausted=True)

        return wrapper

    return decorator
