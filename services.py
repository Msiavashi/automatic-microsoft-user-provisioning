import httpx
import os
from typing import Dict


class AzureAutoOBRClient:
    def __init__(self):
        self.api_key = os.environ.get('PASSKEY_OBR_API_KEY')
        self.base_url = os.environ.get('AUTHENAPI_URL')
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

    def _send_request(self, method: str, url: str, params: Dict = None, data: Dict = None):
        with httpx.Client() as client:
            response = client.request(
                method, url, params=params, headers=self.headers, json=data
            )
            return response

    def update_request_status(
        self, user_id: str, requestId: str, status: str, description: str
    ):
        """
        Update the status of a request in the system.

        Parameters:
        - user_id (str): The unique identifier of the user associated with the request.
        - requestId (str): The unique identifier of the request to be updated.
        - issuerId (str): The unique identifier of the issuer responsible for the request.
        - status (str): The new status of the request. Must be one of the following values: 'DONE', 'WAITING', 'FAILED'.
        - description (str): A description of the status update.

        Raises:
        - Exception: If there is an issue with the HTTP request or response.

        Usage:
        - Call this method to update the status of a request in the system.
        """
        # Construct the URL for the PATCH request
        # url = f"{self.base_url}/internal/azureAutoOBR"
        url = f"http://localhost:8080/azureAutoOBR"

        # Define the request parameters
        params = {
            "requestId": requestId,
            "userId": user_id,
        }

        # Define the data to be sent in the request body
        data = {"status": status, "description": description}
        print(data)
        try:
            # Send the PATCH request and handle the response
            response = self._send_request(
                "PATCH", url, params=params, data=data)
            return self._handle_response(response)
        except Exception as e:
            # TODO: handle the exceptions
            print(f"Error sending request: {e}")

    # def notify_azure_auto_obr(self, azure_auto_obr_id: str):
    #     url = f"{self.base_url}/internal/notifyAzureAutoOBR"
    #     params = {"azureAutoOBRId": azure_auto_obr_id}

    #     response = self._send_request("GET", url, params=params)
    #     self._handle_response(response)

    def _handle_response(self, response):
        if response.status_code == httpx.codes.OK:
            json_response = response.json()
            # Process the response data here
            print(json_response)
        else:
            # Request encountered an error
            print("Request failed with status code:", response.status_code)
            print("Error:", response.text)
