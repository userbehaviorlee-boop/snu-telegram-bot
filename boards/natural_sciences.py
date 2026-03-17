"""
natural_sciences.py
서울대학교 자연과학대학 공지사항 게시판 파서
대상 URL: https://science.snu.ac.kr/news/announcement?sc=y

실제 HTML 구조 (2024년 기준):
  <table class="table text-center board-list">
    <tbody>
      <tr>
        <td class="text-center">번호</td>
        <td class="text-center d-none d-md-none d-lg-table-cell">분류</td>
        <td class="board-title"><a href="/news/announcement?md=v&bbsidx=5419">제목</a></td>
        <td class="text-center d-none d-md-none d-lg-table-cell">2026-03-17</td>
        <td class="text-center d-none d-md-none d-lg-table-cell">조회수</td>
      </tr>
    </tbody>
  </table>
"""

import logging
from bs4 import BeautifulSoup, Tag
from boards.base_parser import BaseParser, Post

logger = logging.getLogger(__name__)


class NaturalSciencesParser(BaseParser):
    """자연과학대학 게시판 파서"""

    def parse(self, html: str, max_items: int) -> list[Post]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[Post] = []

        rows = self._find_rows(soup)
        if not rows:
            logger.warning("자연과학대학 파서: 게시글 행을 찾지 못했습니다.")
            return posts

        for row in rows[:max_items]:
            post = self._parse_row(row)
            if post:
                posts.append(post)

        logger.info(f"자연과학대학 파서: {len(posts)}개 게시글 파싱 완료")
        return posts

    def _find_rows(self, soup: BeautifulSoup) -> list[Tag]:
        """실제 구조: table.board-list > tbody > tr"""

        # Primary: class에 "board-list" 포함
        table = soup.find("table", class_="board-list")
        if table:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")  # type: ignore
                if rows:
                    return rows

        # Fallback: tbody가 있는 모든 table
        for tbl in soup.find_all("table"):
            tbody = tbl.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")  # type: ignore
                if rows:
                    return rows

        return []

    def _parse_row(self, row: Tag) -> Post | None:
        try:
            # 제목 링크: td.board-title > a
            title_td = row.find("td", class_="board-title")
            if not title_td:
                # fallback: 세 번째 td
                tds = row.find_all("td")
                title_td = tds[2] if len(tds) > 2 else None

            if not title_td:
                return None

            a_tag = title_td.find("a")  # type: ignore
            if not a_tag:
                return None

            title = a_tag.get_text(strip=True)
            href = str(a_tag.get("href", ""))
            url = self.make_absolute_url(href)

            if not title or not url:
                return None

            # 분류: td[1] (두 번째 td)
            # 날짜: td[3] (네 번째 td)
            tds = row.find_all("td")

            category = ""
            date = ""

            if len(tds) > 1:
                category = tds[1].get_text(strip=True)
            if len(tds) > 3:
                date = tds[3].get_text(strip=True)

            return Post(title=title, url=url, date=date, category=category)

        except Exception as e:
            logger.debug(f"자연과학대학 파서: 행 파싱 실패 - {e}")
            return None
