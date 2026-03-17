# SNU 텔레그램 봇

서울대학교 게시판에 새 글이 올라오면 텔레그램으로 알려주는 봇입니다.

## 감시 대상 게시판

| 게시판 | URL |
|---|---|
| 서울대 공과대학 공지사항 | https://engineering.snu.ac.kr/community/notice |
| 서울대 자연과학대학 공지사항 | https://science.snu.ac.kr/community/notice |

---

## 폴더 구조

```
snu-telegram-bot/
├─ .env                  ← 텔레그램 토큰/채팅ID (직접 만들어야 함)
├─ .env.example          ← .env 작성 예시
├─ .gitignore
├─ README.md
├─ requirements.txt
├─ main.py               ← 실행 진입점
├─ config.json           ← 게시판 목록 설정
├─ seen_posts.json       ← 이미 본 게시글 URL 저장소
├─ boards/
│  ├─ __init__.py
│  ├─ base_parser.py     ← 파서 공통 기반 클래스
│  ├─ engineering.py     ← 공과대학 파서
│  └─ natural_sciences.py ← 자연과학대학 파서
├─ services/
│  ├─ __init__.py
│  ├─ fetcher.py         ← HTTP 크롤링
│  ├─ notifier.py        ← 텔레그램 전송
│  ├─ runner.py          ← 전체 흐름 조율
│  └─ storage.py         ← seen_posts.json 관리
└─ logs/
   └─ app.log            ← 실행 로그 (자동 생성)
```

---

## 설치 방법

### 1. Python 확인

```
python --version
```

Python 3.11 이상이어야 합니다.

### 2. 가상환경 만들기 (선택 권장)

```
python -m venv venv
venv\Scripts\activate
```

### 3. 패키지 설치

```
pip install -r requirements.txt
```

---

## .env 설정 방법

### 1. .env 파일 만들기

프로젝트 루트에 `.env` 파일을 만들고 아래 내용을 붙여넣습니다.

```
TELEGRAM_BOT_TOKEN=여기에_봇_토큰_입력
TELEGRAM_CHAT_ID=여기에_채팅_ID_입력
```

> `.env.example` 파일을 복사해서 이름을 `.env` 로 바꿔도 됩니다.

### 2. 텔레그램 봇 만들기

1. 텔레그램에서 `@BotFather` 를 검색합니다.
2. `/newbot` 명령을 보냅니다.
3. 봇 이름과 유저네임을 입력하면 **토큰**을 받습니다.
4. 받은 토큰을 `TELEGRAM_BOT_TOKEN` 에 입력합니다.

### 3. 채팅 ID 찾는 방법

1. 만든 봇과 텔레그램에서 대화를 시작합니다 (`/start` 전송).
2. 브라우저에서 아래 URL 을 방문합니다.
   `https://api.telegram.org/bot[봇토큰]/getUpdates`
   예) `https://api.telegram.org/bot1234567890:ABC.../getUpdates`
3. 결과 JSON 에서 `"chat": {"id": 12345678}` 부분의 숫자가 채팅 ID 입니다.
4. 그 숫자를 `TELEGRAM_CHAT_ID` 에 입력합니다.

---

## 수동 실행 방법

```
python main.py
```

---

## 최초 실행 안내

**최초 실행 시에는 기존 게시글을 텔레그램으로 보내지 않습니다.**

최초 실행 시 현재 게시판의 글을 모두 "이미 본 글"로 등록만 합니다.
이후 실행부터 새로 올라온 글만 알림이 전송됩니다.

이는 프로그램을 처음 설치했을 때 수백 개의 기존 글이 한꺼번에 전송되는 것을 방지하기 위한 조치입니다.

---

## Windows 작업 스케줄러 등록 방법

### 방법 1: .bat 파일로 실행 (권장)

아래 내용으로 `run_bot.bat` 파일을 만드세요.

```bat
@echo off
cd /d "C:\경로\snu-telegram-bot"
call venv\Scripts\activate
python main.py
```

> `C:\경로\snu-telegram-bot` 부분은 실제 프로젝트 경로로 변경하세요.

### 방법 2: 작업 스케줄러 등록 절차

1. Windows 검색에서 **작업 스케줄러** 를 엽니다.
2. 오른쪽 패널에서 **기본 작업 만들기** 를 클릭합니다.
3. 이름 입력: `SNU 게시판 봇`
4. 트리거: **매일** 선택
5. 시작 시간: `08:00` 입력 (첫 번째 일정)
6. 동작: **프로그램 시작** 선택
7. 프로그램: `C:\경로\snu-telegram-bot\run_bot.bat`
8. 완료 후, 작업을 우클릭 → **속성** → **트리거** 탭 → 트리거 추가
   - `12:00` 두 번째 일정 추가
   - `19:00` 세 번째 일정 추가

### 하루 3회 실행 시간

| 회차 | 시간 |
|---|---|
| 1회 | 오전 8:00 |
| 2회 | 오후 12:00 |
| 3회 | 오후 7:00 |

---

## 게시판 추가/비활성화 방법

`config.json` 을 수정합니다.

```json
{
  "boards": [
    {
      "board_name": "서울대 공과대학",
      "url": "https://engineering.snu.ac.kr/community/notice",
      "parser_name": "engineering",
      "enabled": true,
      "max_items": 20
    }
  ]
}
```

- `enabled: false` 로 바꾸면 해당 게시판은 건너뜁니다.
- `max_items` 는 한 번에 확인할 최대 게시글 수입니다.

---

## 로그 확인

```
logs\app.log
```

로그 파일은 5MB 가 넘으면 자동으로 새 파일이 생성되고, 최대 3개까지 유지됩니다.

---

## 자주 발생하는 문제

| 증상 | 원인 | 해결 |
|---|---|---|
| 텔레그램 메시지가 안 옴 | .env 설정 오류 | TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 재확인 |
| 게시글 파싱 0개 | 게시판 HTML 구조 변경 | logs/app.log 확인 후 파서 selector 수정 |
| ModuleNotFoundError | 패키지 미설치 | `pip install -r requirements.txt` 재실행 |
| 최초 실행인데 알림 없음 | 정상 동작 | 다음 실행부터 새 글만 알림 전송 |
