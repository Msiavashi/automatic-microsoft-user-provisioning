import httpx
from logger import LoggerManager
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()


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
        endpoint = f"/internal/tap/{user_id}/{obr_request_issuer}"
        response = self._make_request("GET", endpoint)

        if response:
            tap = response.get("temporaryAccessPass")
            if tap:
                self.logger.info(f"TAP value: {tap}")
                return tap
            else:
                raise ValueError(
                    f"No TAP found for user {user_id} with issuer {obr_request_issuer}")
        else:
            raise ConnectionError(
                f"Failed to retrieve TAP for user {user_id} with issuer {obr_request_issuer}")

    def update_azure_auto_obr(self, user_id: str, azure_auto_obr_id: str, obr_request_issuer_id: str, status: int, description: str) -> dict:
        """
        Update Azure Auto OBR with provided details.

        :param user_id: ID of the user
        :param azure_auto_obr_id: Azure Auto OBR ID
        :param obr_request_issuer_id: OBR request issuer ID
        :param status: Status code
        :param description: Description text
        :return: Response data or error message
        """
        endpoint = "/internal/azureAutoOBR"
        params = {
            "azureAutoOBRId": azure_auto_obr_id,
            "userId": user_id,
            "obrRequestIssuerId": obr_request_issuer_id
        }
        data = {"status": status, "description": description}

        response = self._make_request(
            "PATCH", endpoint, params=params, json=data)
        return response or {"error": "Failed to update Azure Auto OBR"}

    def notify_azure_auto_obr(self, azure_auto_obr_id: str) -> dict:
        """
        Notify Azure Auto OBR with the provided OBR ID.

        :param azure_auto_obr_id: Azure Auto OBR ID
        :return: Response data or error message
        """
        endpoint = "/internal/notifyAzureAutoOBR"
        params = {"azureAutoOBRId": azure_auto_obr_id}

        response = self._make_request("GET", endpoint, params=params)
        return response or {"error": "Failed to notify Azure Auto OBR"}

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
                    return None
        except Exception as e:
            self.logger.error(
                f"An error occurred while making a request to {url}. Error: {str(e)}")
            return None
