import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import logger

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

class HttpClient:
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=lambda retry_state: logger.warning(f"Retrying request... Attempt {retry_state.attempt_number}")
    )
    def get(url: str, params: dict = None, headers: dict = None, timeout: int = 15) -> httpx.Response:
        request_headers = DEFAULT_HEADERS.copy()
        if headers:
            request_headers.update(headers)
        
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(url, params=params, headers=request_headers, timeout=timeout)
            response.raise_for_status()
            return response

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=lambda retry_state: logger.warning(f"Retrying request... Attempt {retry_state.attempt_number}")
    )
    def post(url: str, json_data: dict = None, headers: dict = None, timeout: int = 15) -> httpx.Response:
        request_headers = DEFAULT_HEADERS.copy()
        if headers:
            request_headers.update(headers)
        
        with httpx.Client(follow_redirects=True) as client:
            response = client.post(url, json=json_data, headers=request_headers, timeout=timeout)
            response.raise_for_status()
            return response
