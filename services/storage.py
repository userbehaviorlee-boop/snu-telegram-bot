"""
storage.py
seen_posts.json 파일을 읽고 쓰는 모듈.

파일 구조 예시:
{
    "서울대 공과대학": [
        "https://engineering.snu.ac.kr/notice/123",
        "https://engineering.snu.ac.kr/notice/124"
    ],
    "서울대 자연과학대학": [
        "https://science.snu.ac.kr/notice/456"
    ]
}
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# seen_posts.json 파일 경로 (main.py 와 같은 폴더)
SEEN_POSTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seen_posts.json")


def load_seen_posts() -> dict[str, list[str]]:
    """
    seen_posts.json 을 읽어서 반환한다.
    파일이 없거나 손상되면 빈 딕셔너리를 반환한다.
    """
    if not os.path.exists(SEEN_POSTS_FILE):
        logger.info("seen_posts.json 파일 없음. 빈 목록으로 시작합니다.")
        return {}

    try:
        with open(SEEN_POSTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 혹시 list 가 아닌 값이 들어있으면 무시
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"seen_posts.json 읽기 실패: {e}")
        return {}


def save_seen_posts(seen: dict[str, list[str]]) -> None:
    """
    seen_posts 딕셔너리를 seen_posts.json 에 저장한다.
    """
    try:
        with open(SEEN_POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(seen, f, ensure_ascii=False, indent=2)
        logger.debug("seen_posts.json 저장 완료")
    except OSError as e:
        logger.error(f"seen_posts.json 저장 실패: {e}")


def is_new_post(seen: dict[str, list[str]], board_name: str, url: str) -> bool:
    """
    해당 URL 이 이미 본 게시글인지 확인한다.
    처음 보는 URL 이면 True, 이미 본 URL 이면 False 를 반환한다.
    """
    seen_urls = seen.get(board_name, [])
    return url not in seen_urls


def mark_as_seen(seen: dict[str, list[str]], board_name: str, url: str) -> None:
    """
    URL 을 seen 목록에 추가한다.
    (파일 저장은 runner.py 에서 일괄 처리)
    """
    if board_name not in seen:
        seen[board_name] = []
    if url not in seen[board_name]:
        seen[board_name].append(url)


def filter_new_posts(
    seen: dict[str, list[str]],
    board_name: str,
    posts: list[dict],
) -> list[dict]:
    """
    posts 목록 중에서 아직 본 적 없는 게시글만 골라서 반환한다.
    중복 URL 도 여기서 제거한다 (deduplicate).
    """
    new_posts = []
    seen_in_this_run: set[str] = set()  # 이번 실행에서 중복 방지용

    for post in posts:
        url = post.get("url", "")
        if not url:
            continue
        # 이미 저장된 URL 이거나 이번 실행에서 이미 처리한 URL 이면 건너뜀
        if not is_new_post(seen, board_name, url) or url in seen_in_this_run:
            continue
        new_posts.append(post)
        seen_in_this_run.add(url)

    return new_posts
