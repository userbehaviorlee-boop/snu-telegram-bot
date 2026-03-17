"""
fetcher.py
HTTP 요청을 담당하는 모듈.

- requests.Session 재사용 (연결 효율화)
- User-Agent 헤더 포함 (봇 차단 방지)
- 실패 시 최대 3번까지 재시도 (retry + backoff)
"""

import logging
import time
import requests
from requests import Session, Response

logger = logging.getLogger(__name__)

# 브라우저처럼 보이게 하는 User-Agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# 재시도 설정
MAX_RETRIES = 3          # 최대 재시도 횟수
RETRY_DELAY = 2.0        # 첫 번째 재시도 대기 시간 (초)
TIMEOUT = 15             # 요청 타임아웃 (초)


def create_session() -> Session:
    """공통 헤더가 설정된 requests.Session 을 만들어 반환한다."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    })
    return session


def fetch_html(session: Session, url: str) -> str | None:
    """
    주어진 URL 의 HTML 을 가져온다.
    실패 시 MAX_RETRIES 번까지 재시도한다.

    성공하면 HTML 문자열을 반환하고,
    모두 실패하면 None 을 반환한다.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(f"요청 시도 {attempt}/{MAX_RETRIES}: {url}")
            response: Response = session.get(url, timeout=TIMEOUT)
            response.raise_for_status()  # 4xx, 5xx 에러면 예외 발생
            response.encoding = response.apparent_encoding  # 한글 인코딩 자동 감지
            logger.debug(f"요청 성공: {url} (상태코드 {response.status_code})")
            return response.text

        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP 에러 (시도 {attempt}/{MAX_RETRIES}): {e}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"연결 에러 (시도 {attempt}/{MAX_RETRIES}): {e}")
        except requests.exceptions.Timeout:
            logger.warning(f"타임아웃 (시도 {attempt}/{MAX_RETRIES}): {url}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"요청 실패 (시도 {attempt}/{MAX_RETRIES}): {e}")

        # 마지막 시도가 아니면 대기 후 재시도 (지수 백오프)
        if attempt < MAX_RETRIES:
            wait = RETRY_DELAY * (2 ** (attempt - 1))  # 2초, 4초, 8초 ...
            logger.info(f"{wait:.0f}초 후 재시도합니다...")
            time.sleep(wait)

    logger.error(f"최대 재시도 횟수 초과. URL 포기: {url}")
    return None
