"""
runner.py
전체 실행 흐름을 조율하는 모듈.

실행 순서:
1. config.json 읽기
2. seen_posts.json 읽기
3. 각 게시판별로:
   a. HTML 크롤링
   b. 게시글 파싱
   c. 새 글 필터링
   d. 최초 실행 여부 판단
      - 최초 실행이면: 현재 글을 모두 seen 처리만 하고 전송하지 않음
      - 이후 실행이면: 새 글을 텔레그램으로 전송
4. seen_posts.json 저장
"""

import json
import logging
import os
from requests import Session

from boards import PARSER_MAP
from services.fetcher import create_session, fetch_html
from services.notifier import notify_board
from services.storage import (
    filter_new_posts,
    load_seen_posts,
    mark_as_seen,
    save_seen_posts,
)

logger = logging.getLogger(__name__)

# config.json 파일 경로
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def load_config() -> dict:
    """config.json 을 읽어서 반환한다."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"config.json 읽기 실패: {e}")
        return {"boards": []}


def is_first_run(seen: dict, board_name: str) -> bool:
    """
    해당 게시판이 최초 실행인지 확인한다.
    seen_posts.json 에 게시판 키 자체가 없으면 최초 실행으로 판단한다.
    """
    return board_name not in seen


def run_all_boards() -> None:
    """
    모든 게시판을 순서대로 처리하는 메인 함수.
    main.py 에서 이 함수를 호출한다.
    """
    config = load_config()
    boards = config.get("boards", [])

    if not boards:
        logger.warning("config.json 에 게시판이 없습니다.")
        return

    # seen_posts.json 불러오기
    seen = load_seen_posts()

    # HTTP 세션 한 번 생성 후 재사용
    session: Session = create_session()

    for board in boards:
        # enabled: false 인 게시판은 건너뜀
        if not board.get("enabled", True):
            logger.info(f"[{board['board_name']}] 비활성화됨 → 건너뜁니다.")
            continue

        board_name: str = board["board_name"]
        url: str = board["url"]
        parser_name: str = board["parser_name"]
        max_items: int = board.get("max_items", 20)

        logger.info(f"=== {board_name} 처리 시작 ===")

        # ── 1. 파서 선택 ─────────────────────────────────────────
        parser_class = PARSER_MAP.get(parser_name)
        if not parser_class:
            logger.error(f"알 수 없는 parser_name: {parser_name}")
            continue

        parser = parser_class(board_url=url)

        # ── 2. HTML 크롤링 ───────────────────────────────────────
        html = fetch_html(session, url)
        if html is None:
            logger.error(f"{board_name}: HTML 가져오기 실패 → 건너뜁니다.")
            continue

        # ── 3. 파싱 ─────────────────────────────────────────────
        try:
            posts = parser.parse(html, max_items)
        except Exception as e:
            logger.error(f"{board_name}: 파싱 중 예외 발생 → {e}")
            continue

        if not posts:
            logger.warning(f"{board_name}: 파싱된 게시글이 없습니다.")
            continue

        logger.info(f"{board_name}: 총 {len(posts)}개 게시글 파싱됨")

        # ── 4. 최초 실행 판단 ────────────────────────────────────
        first_run = is_first_run(seen, board_name)

        if first_run:
            # 최초 실행: 현재 글을 모두 seen 처리만 하고 알림 없음
            logger.info(f"{board_name}: 최초 실행 → 현재 게시글을 seen 처리만 합니다.")
            for post in posts:
                if post.get("url"):
                    mark_as_seen(seen, board_name, post["url"])
            logger.info(f"{board_name}: {len(posts)}개 게시글을 seen 처리했습니다.")
            continue

        # ── 5. 새 글 필터링 ──────────────────────────────────────
        new_posts = filter_new_posts(seen, board_name, posts)
        logger.info(f"{board_name}: 새 글 {len(new_posts)}개 발견")

        # ── 6. 텔레그램 전송 ─────────────────────────────────────
        if new_posts:
            notify_board(board_name, new_posts)
            # 전송 성공 여부와 무관하게 seen 처리
            # (실패해도 다음 실행에서 중복 방지)
            for post in new_posts:
                if post.get("url"):
                    mark_as_seen(seen, board_name, post["url"])
        else:
            logger.info(f"{board_name}: 새 글 없음")

    # ── 7. seen_posts.json 저장 ──────────────────────────────────
    save_seen_posts(seen)
    logger.info("=== 전체 처리 완료 ===")
