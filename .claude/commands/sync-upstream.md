---
description: 공식 crawl4ai 저장소의 새 릴리스를 확인하고 변경 사항을 이 MCP 서버 소스에 반영
argument-hint: [targetVersion]
---

공식 저장소(`unclecode/crawl4ai`)의 새 릴리스를 확인하고, 이 저장소의 `crawl4ai` 의존성을 올린 뒤 깨지거나 바뀐 부분을 소스에 반영한다.

## 인자

`$ARGUMENTS`가 targetVersion이다 (없을 수 있음). 없으면 최신 정식 릴리스를 대상으로 한다. pre-release는 인자로 명시했을 때만 대상으로 삼는다.

## 1. 버전 확인

- 현재 버전: `uv pip show crawl4ai`의 설치 버전과 `pyproject.toml`의 `crawl4ai>=` 하한을 함께 확인한다. `uv.lock`은 `.gitignore` 대상이라 기기마다 다를 수 있다.
- 대상 버전: `gh api 'repos/unclecode/crawl4ai/releases?per_page=10' --jq '.[] | select(.prerelease == false) | .tag_name + " " + .published_at'`. `gh`를 쓸 수 없으면 `https://pypi.org/pypi/crawl4ai/json`의 `info.version`을 쓴다.
- 현재 버전이 대상 버전과 같거나 더 높으면 "최신 상태"라고 보고하고 끝낸다. 파일은 수정하지 않는다.

## 2. 변경 사항 조사

- 현재 버전 이후 대상 버전까지의 릴리스 노트(`gh api repos/unclecode/crawl4ai/releases/tags/<tag> --jq .body`)와 `CHANGELOG.md`(`gh api repos/unclecode/crawl4ai/contents/CHANGELOG.md --jq .content | base64 -d`)를 읽는다.
- 이 저장소가 실제로 쓰는 crawl4ai API를 하드코딩된 목록이 아니라 소스에서 직접 뽑는다: `grep -n "crawl4ai\|CrawlerRunConfig\|BrowserConfig\|CrawlResult\|CacheMode\|ExtractionStrategy\|arun\|result\." src/`.
- 아래 항목에 해당하는 변경만 골라낸다.
  - 사용 중인 클래스, 함수, 파라미터의 제거, 이름 변경, 기본값 변경, deprecated 처리
  - `CrawlResult` 필드(`success`, `error_message`, `markdown`, `extracted_content`, `screenshot`)와 `arun` 반환 타입(`CrawlResultContainer`)의 변화
  - `JsonCssExtractionStrategy` 스키마 형식 변화
  - 브라우저 붕괴 감지 문자열(`_looks_like_browser_crash*`)에 영향을 주는 Playwright 오류 메시지나 브라우저 재활용 방식의 변화
  - 브라우저 설치 절차(`crawl4ai-setup`)나 Python 버전 요구 사항의 변화
- 확인할 수 없는 항목은 추측하지 말고 "확인 불가"로 남긴다.

## 3. 업그레이드

- `uv add "crawl4ai>=<대상 버전>"`으로 하한을 올리고 lock과 환경을 갱신한다. 다른 의존성의 범위는 건드리지 않는다.
- 릴리스 노트에 Playwright나 브라우저 버전 변경이 있으면 `uv run crawl4ai-setup`을 실행한다.

## 4. 소스 반영

- 2단계에서 고른 변경 중 이 저장소에 영향이 있는 것만 `src/crawl4ai_local/server.py`에 반영한다. 관련 없는 리팩터링은 하지 않는다.
- MCP 도구의 이름, 인자, 반환 형식은 바꾸지 않는다. upstream 변경 때문에 바꿀 수밖에 없다면 수정하기 전에 사용자에게 묻는다.
- 새로 생긴 upstream 기능은 구현하지 않는다. 쓸 만한 기능은 보고에 제안으로만 적는다.
- 도구의 동작이나 설치 절차가 바뀌었으면 `README.md`와 `README.ko.md`를 함께 갱신한다.

## 5. 검증

아래를 모두 실행하고 결과를 그대로 보고한다. 실패를 규칙 비활성화, `# type: ignore`, `cast`로 덮지 않는다.

```
uv run ruff check
uv run flake8 src tests
uv run mypy
uv run pytest -q
```

그다음 세 도구를 실제로 호출하는 스모크 테스트를 스크래치 디렉터리의 임시 스크립트로 실행한다 (저장소에는 넣지 않는다).

- `crawl_markdown("https://example.com")`: 본문 마크다운이 반환되는지
- `crawl_structured("https://books.toscrape.com/", "article.product_pod", {"title": "h3 a@title", "price": ".price_color:text"})`: 제목과 가격이 든 JSON 배열이 반환되는지
- `crawl_screenshot("https://example.com", "<스크래치 디렉터리>/shot.png")`: 파일이 생성되는지
- 끝나면 `shutdown_crawler()`를 호출한다.

## 6. 보고

- 버전: 이전 → 이후
- 이 저장소에 영향이 있던 upstream 변경과 각각의 반영 내용 (파일:줄)
- 영향 없음으로 판단한 주요 변경 (한 줄씩)
- 검증 결과
- 쓸 만한 새 upstream 기능 제안 (있으면)

커밋은 하지 않는다.
