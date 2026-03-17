"""
main.py
프로그램 진입점.

실행 방법:
    python main.py

이 파일은 다음 두 가지를 한다:
1. 로깅 설정 (콘솔 + 파일)
2. runner.run_all_boards() 호출
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

# ── 환경변수 로드 (.env 파일) ────────────────────────────────────────
# main.py 와 같은 폴더의 .env 파일을 읽는다
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


def setup_logging() -> None:
    """
    로깅을 설정한다.
    - 콘솔: INFO 레벨 이상 출력
    - 파일: DEBUG 레벨 이상, logs/app.log 에 저장 (최대 5MB, 최대 3개 파일 유지)
    """
    # logs 폴더가 없으면 자동 생성
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    # 로그 포맷: 시간 | 레벨 | 모듈명 | 메시지
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 전체 최저 레벨

    # 콘솔 핸들러 (INFO 이상만 보임)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 파일 핸들러 (DEBUG 이상, 최대 5MB, 백업 3개)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def main() -> None:
    """프로그램 메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("SNU 텔레그램 봇 시작")

    try:
        # runner 를 여기서 import 하는 이유:
        # setup_logging() 이 먼저 실행된 후 import 되어야
        # 하위 모듈의 logger 가 올바르게 설정되기 때문
        from services.runner import run_all_boards
        run_all_boards()
    except Exception as e:
        logger.critical(f"예상치 못한 오류로 프로그램 종료: {e}", exc_info=True)
        sys.exit(1)

    logger.info("SNU 텔레그램 봇 종료")


if __name__ == "__main__":
    main()
