import httpx
import logging
import os
from typing import Dict


class Config:
    @staticmethod
    def get_api_key():
        return os.environ.get('PASSKEY_OBR_API_KEY')

    @staticmethod
    def get_base_url():
        return os.environ.get('AUTHNAPI_URL')


class AzureAutoOBRClient:
    def __init__(self, timeout=10):
        self.api_key = Config.get_api_key()
        self.base_url = Config.get_base_url()
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }
        self.timeout = timeout

    def _send_request(self, method: str, url: str, params: Dict = None, data: Dict = None):
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method, url, params=params, headers=self.headers, json=data
            )
            return response

    def update_request_status(
            self, user_id: str, requestId: str, status: str, description: str
    ):
        url = f"{self.base_url}/internal/azureAutoOBR"
        params = {"requestId": requestId, "userId": user_id}
        data = {"status": status, "description": description}

        try:
            response = self._send_request("PATCH", url, params=params, data=data)
            response.raise_for_status()
            return self._handle_response(response)
        except httpx.HTTPError as http_error:
            logging.error(f"HTTP error: {http_error}")
        except Exception as e:
            logging.error(f"Error sending request: {e}")

    def _handle_response(self, response):
        if response.status_code == httpx.codes.OK:
            json_response = response.json()
            logging.debug(json_response)
        else:
            logging.debug("Request failed with status code:", response.status_code)
            logging.debug("Error:", response.text)
