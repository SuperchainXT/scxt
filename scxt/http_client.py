from typing import Any, Dict, Optional, Union, Type
from pydantic import BaseModel, Field, AnyHttpUrl

import requests
from requests.exceptions import HTTPError


class HTTPConfig(BaseModel):
    """HTTP client configuration model."""

    base_url: AnyHttpUrl = Field(..., description="Base URL for the API")
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")
    verbose: bool = Field(
        default=False, description="Enable verbose logging for requests"
    )


class HTTPClient:
    """HTTP client for making API requests.

    Args:
        config (Union[Dict[str, Any], HTTPConfig]): Client configuration.
    """

    def __init__(self, config: Union[Dict[str, Any], HTTPConfig]):
        self.config = HTTPConfig.model_validate(config)
        self.base_url = self.config.base_url
        self.timeout = self.config.timeout
        self.session = self._setup_session()

    def _setup_session(self):
        """Sets up an HTTP session.

        Returns:
            requests.Session: Configured session object.
        """
        return requests.Session()

    def _handle_exception(self, response):
        """Handles HTTP exceptions.

        Args:
            response (Response): The HTTP response object.

        Raises:
            HTTPError: If response indicates an error occurred.
        """
        http_error_msg = ""
        reason = response.reason

        if 400 <= response.status_code < 500:
            if (
                response.status_code == 403
                and "'error_details':'Missing required scopes'" in response.text
            ):
                http_error_msg = f"{response.status_code} Client Error: Missing Required Scopes. Please verify your API keys include the necessary permissions."
            else:
                http_error_msg = (
                    f"{response.status_code} Client Error: {reason} {response.text}"
                )
        elif 500 <= response.status_code < 600:
            http_error_msg = (
                f"{response.status_code} Server Error: {reason} {response.text}"
            )

        if http_error_msg:
            self.logger.error(f"HTTP Error: {http_error_msg}")
            raise HTTPError(http_error_msg, response=response)

    def get(self, url_path, params: Optional[dict] = None, **kwargs) -> Dict[str, Any]:
        """Sends a GET request.

        Args:
            url_path (str): The URL path.
            params (dict, optional): The query parameters.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            Dict[str, Any]: The response data.
        """
        params = params or {}

        if kwargs:
            params.update(kwargs)

        return self.prepare_and_send_request("GET", url_path, params, data=None)

    def get_validated(
        self,
        url_path,
        request_model: Type[BaseModel],
        response_model: Type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        """Sends a GET request including type validation of both the input and output from provided models.

        Args:
            url_path (str): The URL path.
            **kwargs: Includes all arguments to pass to the request.

        Returns:
            Dict[str, Any]: The response data, validated against the response_model.
        """
        validated_params = request_model.model_validate(kwargs, by_name=True)
        params = validated_params.model_dump(
            mode="json", exclude_none=True, by_alias=True
        )

        response_data = self.prepare_and_send_request(
            "GET", url_path, params, data=None
        )
        validated_response = response_model.model_validate(response_data)
        return validated_response

    def post(
        self,
        url_path,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Sends a POST request.

        Args:
            url_path (str): The URL path.
            params (dict, optional): The query parameters.
            data (dict, optional): The request body.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            Dict[str, Any]: The response data.
        """
        data = data or {}

        if kwargs:
            data.update(kwargs)

        return self.prepare_and_send_request("POST", url_path, params, data)

    def put(
        self,
        url_path,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Sends a PUT request.

        Args:
            url_path (str): The URL path.
            params (dict, optional): The query parameters.
            data (dict, optional): The request body.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            Dict[str, Any]: The response data.
        """
        data = data or {}

        if kwargs:
            data.update(kwargs)

        return self.prepare_and_send_request("PUT", url_path, params, data)

    def delete(
        self,
        url_path,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Sends a DELETE request.

        Args:
            url_path (str): The URL path.
            params (dict, optional): The query parameters.
            data (dict, optional): The request body.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            Dict[str, Any]: The response data.
        """
        data = data or {}

        if kwargs:
            data.update(kwargs)

        return self.prepare_and_send_request("DELETE", url_path, params, data)

    def prepare_and_send_request(
        self,
        http_method,
        url_path,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ):
        """Prepares and sends an HTTP request.

        Args:
            http_method (str): The HTTP method.
            url_path (str): The URL path.
            params (dict, optional): The query parameters.
            data (dict, optional): The request body.

        Returns:
            Dict[str, Any]: The response data.
        """
        headers = self.set_headers(http_method, url_path)

        if params is not None:
            params = {
                key: str(value).lower() if isinstance(value, bool) else value
                for key, value in params.items()
                if value is not None
            }

        if data is not None:
            data = {key: value for key, value in data.items() if value is not None}

        return self.send_request(http_method, url_path, params, headers, data=data)

    def send_request(self, http_method, url_path, params, headers, data=None):
        """Sends an HTTP request.

        Args:
            http_method (str): The HTTP method.
            url_path (str): The URL path.
            params (dict): The query parameters.
            headers (dict): The request headers.
            data (dict, optional): The request body.

        Returns:
            Dict[str, Any]: The response data.

        Raises:
            HTTPError: If the request fails.
        """
        if data is None:
            data = {}

        url = f"{self.base_url}{url_path}"

        self.logger.debug(f"Sending {http_method} request to {url}")

        response = self.session.request(
            http_method,
            url,
            params=params,
            json=data,
            headers=headers,
            timeout=self.timeout,
        )
        self._handle_exception(response)  # Raise an HTTPError for bad responses

        self.logger.debug(f"Raw response: {response.json()}")

        response_data = response.json()
        return response_data

    def set_headers(self, method, path):
        """Sets the request headers.

        Args:
            method (str): The HTTP method.
            path (str): The URL path.

        Returns:
            dict: The request headers.
        """

        return {
            "Content-Type": "application/json",
        }
