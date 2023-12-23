class MicrosoftAccessPassValidationException(Exception):
    """Occurs when an access pass validation error is found in the console."""
    pass


class OrganizationNeedsMoreInformationException(Exception):
    "Occurs when user needs to take action on their account to be able to login"
    pass


class SecurityKeysLimitException(Exception):
    "Occurs when microsoft display exception related to maximum number of security keys reached"
    pass


class TwoFactorAuthRequiredException(Exception):
    """Occurs when a security key setup requires two-factor authentication."""
    pass


class TAPRetrievalFailureException(Exception):
    """Exception raised for TAP retrieval failures."""
    pass


class RedirectedToPasswordPageException(Exception):
    """Exception raised when redirected to password page instead of TAP page."""
    pass
