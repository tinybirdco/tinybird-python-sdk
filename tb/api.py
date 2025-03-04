from urllib.error import HTTPError
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging
import sys


class API:
    def __init__(
        self,
        token,
        api_url="https://api.tinybird.co",
        version="v0",
        retry_total=1,
        backoff_factor=0.2,
    ):
        self.api_url = api_url.rstrip("/")
        self.version = version
        TOKEN_ERROR = f"Token must be a valid Tinybird token for {self.api_url}. Check the `api_url` param is correct and the token has the right permissions. {self.ui_url()}/tokens"
        if not token:
            logging.critical(TOKEN_ERROR)
            sys.exit(-1)
        self.token = token
        retry = Retry(total=retry_total, backoff_factor=backoff_factor)
        adapter = HTTPAdapter(max_retries=retry)
        self._session = requests.Session()
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        # Rate limit
        self.rate_limit_points = 6
        self.rate_limit_remaining = self.rate_limit_points
        self.rate_limit_reset = 0
        self.retry_after = 1

        # check the token is valid
        try:
            self.get("/datasources")
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logging.error(TOKEN_ERROR)
                sys.exit(-1)

    def ui_url(self):
        return self.api_url.replace("api", "ui")

    def _handle_rate_limit(self) -> None:
        if self.rate_limit_remaining == 0:
            time_to_sleep = min((self.rate_limit_reset - time.time()), 10)
            time_to_sleep = max(time_to_sleep, 1) + 1
            logging.info(f"Waiting {str(time_to_sleep)} seconds before retrying...")
            time.sleep(time_to_sleep)
            logging.info("Retrying")

    def _set_rate_limit(self, response: requests.Response) -> None:
        # Update rate limit fields
        if "X-Ratelimit-Limit" in response.headers.keys():
            self.rate_limit_points = int(response.headers.get("X-Ratelimit-Limit"))
            self.rate_limit_remaining = int(
                response.headers.get("X-Ratelimit-Remaining")
            )
            self.rate_limit_reset = int(response.headers.get("X-Ratelimit-Reset"))
            self.retry_after = int(response.headers.get("Retry-After", 0))

    def send(self, path, method="POST", **kwargs):
        self._handle_rate_limit()
        headers = {"Authorization": "Bearer " + self.token}
        while True:
            url = f"{self.api_url}/{self.version}/{path.lstrip('/')}"
            if method == "POST":
                response = self._session.post(url, headers=headers, **kwargs)
            elif method == "DELETE":
                response = self._session.delete(url, headers=headers, **kwargs)
            else:
                response = self._session.get(url, headers=headers, **kwargs)
            self._set_rate_limit(response)

            if response.status_code == 429:
                logging.warning(
                    f"Too many requests, you can do {self.rate_limit_points} requests per minute..."
                )
                self._handle_rate_limit()
            else:
                break
        response.raise_for_status()
        return response

    def post(self, path, **kwargs):
        return self.send(path, method="POST", **kwargs)

    def get(self, path, **kwargs):
        return self.send(path, method="GET", **kwargs)

    def delete(self, path, **kwargs):
        return self.send(path, method="DELETE", **kwargs)
