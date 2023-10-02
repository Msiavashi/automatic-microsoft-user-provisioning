import httpx
from logger import LoggerManager
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()


class TAPRetrievalFailureException(Exception):
    """Exception raised for TAP retrieval failures."""
    pass


class TAPManager:
    """TAP Management class to handle various TAP related operations."""

    def __init__(self):
        self.logger = LoggerManager.setup_logger("TAP")
        self.base_url = os.getenv("AUTHNAPI_URL")
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": os.getenv("PASSKEY_OBR_API_KEY", ""),
        }

    def retrieve_TAP(self, user_id: str, obr_request_issuer: str) -> str:
        """
        Retrieve Temporary Access Pass (TAP) for a given user and issuer.

        :param user_id: ID of the user
        :param obr_request_issuer: OBR request issuer ID
        :return: Temporary Access Pass or raises an exception if not found
        """
        try:
            endpoint = f"/internal/tap/{user_id}/{obr_request_issuer}"
            response = self._make_request("GET", endpoint)
            self.logger.debug(f"TAP API response: {response}")
            if response:
                tap = response.get("temporaryAccessPass")
                if tap:
                    self.logger.info(f"TAP value: {tap}")
                    return tap
                else:
                    raise ValueError(
                        f"No TAP found for user {user_id} with issuer {obr_request_issuer}")
            else:
                self.logger.debug(
                    f"Failed to retrieve TAP for user {user_id} with issuer {obr_request_issuer}")
                raise TAPRetrievalFailureException(
                    f"Failed to retrieve TAP")
        except Exception as e:
            raise TAPRetrievalFailureException(e)


    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Private helper method to make HTTP requests and handle common response patterns.

        :param method: HTTP method (GET, POST, PATCH, etc.)
        :param endpoint: API endpoint
        :param kwargs: Additional arguments for the request
        :return: Response data or None in case of failure
        """
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.Client() as client:
                response = client.request(
                    method, url, headers=self.headers, **kwargs)

                if response.status_code == httpx.codes.OK:
                    self.logger.debug(f"Request to {url} was successful.")
                    return response.json()
                else:
                    self.logger.error(
                        f"Request to {url} failed with status code: {response.status_code}")
                    self.logger.error(f"Error: {response.text}")
                    if (response.json().get("message", None)):
                        raise TAPRetrievalFailureException(
                            response.json().get("message"))
                    else:
                        raise TAPRetrievalFailureException(
                            "Failed to retrieve TAP due to error from Microsoft.")
        except Exception as e:
            raise
