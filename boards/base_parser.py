"""
base_parser.py
모든 게시판 파서가 공통으로 상속하는 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import TypedDict
from urllib.parse import urljoin, urlparse


# 게시글 하나의 데이터 구조 정의
class Post(TypedDict):
    title: str      # 제목
    url: str        # 게시글 링크 (절대경로)
    date: str       # 날짜 (문자열)
    category: str   # 분류


class BaseParser(ABC):
    """모든 파서의 기본 클래스"""

    def __init__(self, board_url: str):
        # 게시판 기본 URL (상대경로 → 절대경로 변환에 사용)
        self.board_url = board_url
        # URL 의 scheme + netloc (예: https://engineering.snu.ac.kr)
        parsed = urlparse(board_url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"

    def make_absolute_url(self, href: str) -> str:
        """
        상대경로 URL을 절대경로로 변환한다.
        예) /notice/123  →  https://engineering.snu.ac.kr/notice/123
        """
        if not href:
            return ""
        # 이미 http:// 로 시작하면 그대로 반환
        if href.startswith("http://") or href.startswith("https://"):
            return href
        # urljoin 이 상대경로를 자동으로 절대경로로 만들어줌
        return urljoin(self.base_url, href)

    @abstractmethod
    def parse(self, html: str, max_items: int) -> list[Post]:
        """
        HTML 문자열을 받아서 Post 목록을 반환한다.
        각 파서(engineering, natural_sciences)가 이 메서드를 구현한다.
        """
        ...
