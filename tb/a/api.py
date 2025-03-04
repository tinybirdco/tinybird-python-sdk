import asyncio
import logging
import sys
import time
from typing import Optional, Dict, Any

import aiohttp
import backoff


class RateLimitError(Exception):
    pass


class AsyncAPI:
    def __init__(
        self,
        token: str,
        api_url: str = "https://api.tinybird.co",
        version: str = "v0",
        retry_total: int = 1,
    ):
        self.api_url = api_url.rstrip("/")
        self.version = version
        TOKEN_ERROR = f"Token must be a valid Tinybird token for {self.api_url}. Check the `api_url` param is correct and the token has the right permissions. {self.ui_url()}/tokens"
        if not token:
            logging.critical(TOKEN_ERROR)
            sys.exit(-1)
        self.token = token
        self._session: Optional[aiohttp.ClientSession] = None

        self.rate_limit_points = 6
        self.rate_limit_remaining = self.rate_limit_points
        self.rate_limit_reset = 0
        self.retry_after = 1
        self.retry_total = retry_total

        self.token_error = TOKEN_ERROR

    def ui_url(self) -> str:
        return self.api_url.replace("api", "ui")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """Support for async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support for async context manager."""
        await self.close()

    async def _handle_rate_limit(self) -> None:
        """Handle rate limiting by waiting if necessary."""
        if self.rate_limit_remaining == 0:
            time_to_sleep = min((self.rate_limit_reset - time.time()), 10)
            time_to_sleep = max(time_to_sleep, 1) + 1
            logging.info(f"Waiting {str(time_to_sleep)} seconds before retrying...")
            await asyncio.sleep(time_to_sleep)
            logging.info("Retrying")

    def _set_rate_limit(self, response: aiohttp.ClientResponse) -> None:
        """Update rate limit information from response headers."""
        headers = response.headers
        if "X-Ratelimit-Limit" in headers:
            self.rate_limit_points = int(headers.get("X-Ratelimit-Limit"))
            self.rate_limit_remaining = int(headers.get("X-Ratelimit-Remaining"))
            self.rate_limit_reset = int(headers.get("X-Ratelimit-Reset"))
            self.retry_after = int(headers.get("Retry-After", "0"))

    async def send(self, path: str, method: str = "POST", **kwargs):
        @backoff.on_exception(
            backoff.expo, (RateLimitError,), max_tries=self.retry_total
        )
        async def _send():
            session = await self._get_session()
            headers = {"Authorization": f"Bearer {self.token}"}

            if "headers" in kwargs:
                kwargs["headers"].update(headers)
            else:
                kwargs["headers"] = headers

            url = f"{self.api_url}/{self.version}/{path.lstrip('/')}"

            while True:
                if method == "POST":
                    response = await session.post(url, **kwargs)
                elif method == "DELETE":
                    response = await session.delete(url, **kwargs)
                else:
                    response = await session.get(url, **kwargs)

                self._set_rate_limit(response)

                if response.status == 429:
                    logging.warning(
                        f"Too many requests, you can do {self.rate_limit_points} requests per minute..."
                    )
                    raise RateLimitError()
                else:
                    break

            if response.status == 403:
                logging.error(self.token_error)

            response.raise_for_status()
            return response

        return await _send()

    async def post(self, path: str, **kwargs) -> aiohttp.ClientResponse:
        """Send a POST request to the Tinybird API."""
        return await self.send(path, method="POST", **kwargs)

    async def get(self, path: str, **kwargs) -> aiohttp.ClientResponse:
        """Send a GET request to the Tinybird API."""
        return await self.send(path, method="GET", **kwargs)

    async def delete(self, path: str, **kwargs) -> aiohttp.ClientResponse:
        """Send a DELETE request to the Tinybird API."""
        return await self.send(path, method="DELETE", **kwargs)

    async def get_json(self, path: str, **kwargs) -> Dict[str, Any]:
        """Send a GET request and return the JSON response."""
        response = await self.get(path, **kwargs)
        return await response.json()

    async def post_json(self, path: str, **kwargs) -> Dict[str, Any]:
        """Send a POST request and return the JSON response."""
        response = await self.post(path, **kwargs)
        return await response.json()

    async def initialize(self) -> None:
        """Initialize the API by checking the token validity."""
        try:
            await self.get("/datasources")
        except aiohttp.ClientResponseError as e:
            if e.status == 403:
                logging.error(self.token_error)
                sys.exit(-1)
