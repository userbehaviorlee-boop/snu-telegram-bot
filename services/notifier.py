"""
notifier.py
텔레그램으로 메시지를 보내는 모듈.

- 게시판별로 묶어서 한 번에 전송
- 새 글이 없으면 메시지를 보내지 않음
- 메시지가 너무 길면 분할 전송 (텔레그램 한 메시지 최대 4096자)
"""

import logging
import os
import time
import requests
from boards.base_parser import Post

logger = logging.getLogger(__name__)

# 텔레그램 메시지 최대 길이
TELEGRAM_MAX_LENGTH = 4096


def get_telegram_credentials() -> tuple[str, str]:
    """
    환경변수에서 텔레그램 봇 토큰과 채팅 ID 를 읽어온다.
    설정이 없으면 예외를 발생시킨다.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token:
        raise ValueError(".env 파일에 TELEGRAM_BOT_TOKEN 이 설정되지 않았습니다.")
    if not chat_id:
        raise ValueError(".env 파일에 TELEGRAM_CHAT_ID 가 설정되지 않았습니다.")

    return token, chat_id


def send_message(token: str, chat_id: str, text: str) -> bool:
    """
    텔레그램 sendMessage API 를 호출해서 메시지를 전송한다.
    성공하면 True, 실패하면 False 를 반환한다.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",          # <b>, <a> 태그 사용 가능
        "disable_web_page_preview": True,  # 링크 미리보기 끄기
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.debug("텔레그램 메시지 전송 성공")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"텔레그램 HTTP 에러: {e} | 응답: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"텔레그램 전송 실패: {e}")
        return False


def build_board_message(board_name: str, posts: list[Post]) -> str:
    """
    게시판 이름과 새 게시글 목록을 받아서
    텔레그램에 보낼 메시지 문자열을 만든다.

    예시 출력:
    [서울대 공과대학] 새 글 2건

    1. 제목
    분류: 일반
    날짜: 2024-01-15
    https://...
    """
    count = len(posts)
    lines = [f"<b>[{board_name}] 새 글 {count}건</b>\n"]

    for i, post in enumerate(posts, start=1):
        title = post.get("title", "(제목 없음)")
        url = post.get("url", "")
        date = post.get("date", "")
        category = post.get("category", "")

        block = f"{i}. {title}"
        if category:
            block += f"\n분류: {category}"
        if date:
            block += f"\n날짜: {date}"
        if url:
            block += f"\n{url}"

        lines.append(block)

    return "\n\n".join(lines)


def split_message(text: str, max_length: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """
    텔레그램 메시지 최대 길이를 넘으면 여러 조각으로 나눈다.
    단락(\n\n) 기준으로 분리한다.
    """
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    current_chunk = ""

    paragraphs = text.split("\n\n")
    for para in paragraphs:
        candidate = current_chunk + ("\n\n" if current_chunk else "") + para
        if len(candidate) <= max_length:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def notify_board(board_name: str, posts: list[Post]) -> None:
    """
    게시판 하나의 새 글 목록을 텔레그램으로 전송한다.
    새 글이 없으면 아무것도 하지 않는다.
    """
    if not posts:
        logger.info(f"{board_name}: 새 글 없음 → 텔레그램 전송 생략")
        return

    try:
        token, chat_id = get_telegram_credentials()
    except ValueError as e:
        logger.error(str(e))
        return

    message = build_board_message(board_name, posts)
    chunks = split_message(message)

    for i, chunk in enumerate(chunks, start=1):
        success = send_message(token, chat_id, chunk)
        if success:
            logger.info(f"{board_name}: 텔레그램 전송 완료 ({i}/{len(chunks)})")
        else:
            logger.error(f"{board_name}: 텔레그램 전송 실패 ({i}/{len(chunks)})")

        # 연속 메시지 전송 시 API 제한 방지용 짧은 대기
        if i < len(chunks):
            time.sleep(1)
