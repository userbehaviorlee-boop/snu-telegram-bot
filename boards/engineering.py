"""
engineering.py
서울대학교 공과대학 공지사항 게시판 파서
대상 URL: https://eng.snu.ac.kr/snu/bbs/BMSR00004/list.do?menuNo=200176

실제 HTML 구조 (2024년 기준):
  <table class="tbl-st1">
    <tbody>
      <tr>
        <td class="no">번호</td>
        <td class="label">분류</td>
        <td class="tal"><a href="view.do?boardId=...&menuNo=200176">제목</a></td>
        <td class="file">첨부파일</td>
        <td class="date">2026.03.16</td>
        ...
      </tr>
    </tbody>
  </table>
"""

import re
import logging
from bs4 import BeautifulSoup, Tag
from boards.base_parser import BaseParser, Post

logger = logging.getLogger(__name__)


class EngineeringParser(BaseParser):
    """공과대학 게시판 파서"""

    def parse(self, html: str, max_items: int) -> list[Post]:
        soup = BeautifulSoup(html, "html.parser")
        posts: list[Post] = []

        rows = self._find_rows(soup)
        if not rows:
            logger.warning("공과대학 파서: 게시글 행을 찾지 못했습니다.")
            return posts

        for row in rows[:max_items]:
            post = self._parse_row(row)
            if post:
                posts.append(post)

        logger.info(f"공과대학 파서: {len(posts)}개 게시글 파싱 완료")
        return posts

    def _find_rows(self, soup: BeautifulSoup) -> list[Tag]:
        """실제 구조: table.tbl-st1 > tbody > tr"""

        # Primary: class="tbl-st1"
        table = soup.find("table", class_="tbl-st1")
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
            # 제목 링크: td.tal > a
            title_td = row.find("td", class_="tal")
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

            # jsessionid 제거 (URL 중복 판별 안정성 향상)
            # view.do;jsessionid=XXX?boardId=123 → view.do?boardId=123
            href_clean = re.sub(r";jsessionid=[A-Fa-f0-9]+", "", href)
            url = self.make_absolute_url(href_clean)

            if not title or not url:
                return None

            # 분류: td.label
            category = self._get_td_text(row, "label")

            # 날짜: td.date
            date = self._get_td_text(row, "date")

            return Post(title=title, url=url, date=date, category=category)

        except Exception as e:
            logger.debug(f"공과대학 파서: 행 파싱 실패 - {e}")
            return None

    def _get_td_text(self, row: Tag, class_name: str) -> str:
        """특정 class를 가진 td의 텍스트를 반환한다."""
        td = row.find("td", class_=class_name)
        if td:
            return td.get_text(strip=True)  # type: ignore
        return ""
