# Crawl4ai Local for Windows

[English](./README.md) | [한국어](./README.ko.md)

Windows용 Crawl4ai 로컬 MCP 서버. WSL 환경 없이 Windows에서 바로 실행 가능한 버전입니다.

🤖 대부분의 코드가 AI를 통해 생성되었습니다.

참고:

- <https://github.com/unclecode/crawl4ai>
- <https://docs.crawl4ai.com/>

## 요구 사항

- [uv](https://docs.astral.sh/uv/)
- Python 3.14 (uv로 설치한 Python은 Windows 스마트 앱 컨트롤에 의해 차단될 수 있으니 별도로 설치할 것)

## 설치

```
uv sync
```

## 실행

🚨 이 서버는 stdio 서버라서 네트워크 서버처럼 미리 띄워둘 필요가 없고, 에이전트에 MCP로 연결이 된 상태면 에이전트가 서버 인스턴스를 자동으로 생성됩니다.

```
# "🚀 Crawl4ai MCP server started." 메시지 확인 후 종료할 것
uv run main
```

✅ 웰컴 메시지 확인 후 `ctrl + c`로 종료하고 에이전트에서 MCP를 추가하면 됩니다.

```
# 참고: 디버깅 모드(MCP Inspector)
uv run mcp dev src/crawl4ai_local_for_windows/server.py
```

## 에이전트에 MCP 추가하기

### Claude Code

```
claude mcp add --transport stdio --scope user crawl4ai -- uv run --directory <parent_location>/crawl4ai-local-for-windows main
```

- `parent_location`: `C:/dev/repo` 형태로 작성
- 예: `claude mcp add --transport stdio --scope user crawl4ai -- uv run --directory C:/dev/repo/crawl4ai-local-for-windows main`

```
# MCP 설치 확인
claude mcp list
claude mcp get crawl4ai
```

### Hermes Agent

```
hermes mcp add crawl4ai --command "uv" --args "run" "--directory" "<parent_location>/crawl4ai-local-for-windows" "main"
```

- `parent_location`: `C:/dev/repo` 형태로 작성
- 예: `C:/dev/repo/crawl4ai-local-for-windows`

```
# MCP 설치 확인
hermes mcp list
```

## 도구

### `crawl_markdown(url, wait_seconds=0, wait_selector="")`

URL을 크롤링해서 콘텐츠를 마크다운으로 반환합니다.

### `crawl_structured(url, selector, fields, wait_seconds=0, wait_selector="")`

CSS 셀렉터로 반복 요소를 추출해 JSON으로 반환합니다.

```
crawl_structured(
    url="https://books.toscrape.com/",
    selector="article.product_pod",
    fields={"제목": "h3@title", "가격": ".price_color:text"},
)
# -> [{"제목": "A Light in the Attic", "가격": "£51.77"}, ...]
```

필드 지정 문법:

| 지정문                 | 의미                                          |
| --------------------- | --------------------------------------------- |
| `"td"` 또는 `"td:text"` | 매칭된 요소의 텍스트                             |
| `"a@href"`            | 자식 요소의 속성 (`요소@속성명`)                   |
| `"@data-value"`       | 기준 요소 자신의 속성                             |
| `"td:nth-of-type(1)"` | N번째 요소 — 표준 CSS 사용 (`:eq()`는 미지원) |

두 도구 모두 대기 옵션을 공유합니다 (아래 참조).

### `crawl_screenshot(url, output_path)`

전체 페이지 스크린샷을 캡처해 파일로 저장합니다. 상위 디렉토리는 자동 생성됩니다.

🛡️ **`output_path`는 크롤링을 실행하기 전에 알려진 Windows 시스템 디렉토리 차단 목록**(`C:\Windows`, `C:\Program Files`, `C:\Program Files (x86)`, `C:\ProgramData`, `C:\System Volume Information`, `C:\$Recycle.Bin`, `C:\Users\All Users`, `C:\Users\Default`)과 대조 검사됩니다. `..` 등을 이용한 우회 경로를 포함해 경로가 이 목록 하위로 해석되면 크롤링 없이 즉시 오류 메시지와 함께 거부되어, 에이전트가 실수로 시스템 파일을 덮어쓰는 것을 막습니다. 화이트리스트 방식의 완전한 샌드박싱이 아니라, 실수 방지 수준의 블랙리스트 가드레일입니다.

## 브라우저 재사용 & 크래시 복구

서버는 호출마다 Chromium을 새로 띄우는 대신(기동 비용이 큼), 프로세스 수명 동안 브라우저 인스턴스 하나를 유지합니다. 공유 브라우저가 세션 도중 크래시하면 서버가 이를 감지해 자동 복구합니다:

- 크래시 감지는 Playwright 붕괴 시그니처에만 매칭 — `Target page, context or browser has been closed`, `browser has crashed`, `browsertype.launch` 실패 등. 네트워크 오류/안티봇 차단/타임아웃은 페이지 쪽 원인이므로 새 브라우저로 재시도하지 않습니다.
- 크래시 시: 죽은 인스턴스 폐기 -> 새 인스턴스 기동 -> 재시도, 최대 `_MAX_RECREATE_ATTEMPTS = 2`회.
- 두 실패 경로를 매 시도마다 균등하게 검사: `arun()`이 던지는 예외 및 `result.success=False` + `error_message`에 크래시 메시지가 담겨 돌아오는 경우.
- 마지막 시도에서도 크래시가 감지되면 실패로 보고하지만, 크롤러를 다시 리셋하지는 않습니다 — 해당 정리는 직전 시도에서 이미 끝났고, 여기서 한 번 더 리셋하면 그 사이 다른 요청이 새로 만든 인스턴스를 괜히 파괴할 수 있기 때문입니다.
- 예방적 재활용(예: N페이지마다 갱신)은 의도적으로 Crawl4ai 내장 브라우저 재활용에 맡깁니다. 서버는 실제 붕괴에만 반응합니다.

동시성 참고: 공유 크롤러에 여러 `arun()` 호출이 동시에 들어와도 안전합니다 — Crawl4ai가 내부적으로 페이지 생성을 직렬화하고(`_page_lock`, GH-1198 수정), refcount + LRU로 컨텍스트 수명을 관리합니다. 다중 사이트 동시 스모크 테스트로 검증 완료.

## 대기 옵션 (동적 페이지)

JS로 콘텐츠가 늦게 렌더링되는 동적 페이지에는 `crawl_markdown` / `crawl_structured`의 대기 옵션을 사용하세요.

```
# 방법 1: 고정 시간 대기 (초)
crawl_markdown(url="https://example.com", wait_seconds=5)

# 방법 2: CSS 셀렉터가 나타날 때까지 대기 (지정 시 wait_seconds보다 우선)
crawl_markdown(url="https://example.com", wait_selector="div.result-list")
```

### 검증 결과 (2026-08-25)

3초 후 JS로 콘텐츠를 갱신하는 로컬 테스트 페이지에서 3개 케이스 비교:

| 케이스                        | success | 동적 콘텐츠 캡처                  |
| -------------------------- | ------- | -------------------------- |
| 대기 옵션 없음                   | True    | ❌ "Loading..."만 반환         |
| `wait_seconds=5`           | True    | ✅ 최종 콘텐츠 정확히 캡처            |
| `wait_selector="#dynamic"` | True    | ❌ 초기 HTML에 이미 있는 요소면 즉시 통과 |

### 발견한 점 / 주의 사항

1. `wait_selector`는 "새로 생기는 요소"에만 유효합니다. 초기 HTML에 이미 있는 요소(예: `<article id="dynamic">Loading...</article>`)의 텍스트가 나중에 바뀌는 경우, 셀렉터가 즉시 매칭되어 아무 대기 없이 통과합니다. 텍스트 갱신형 페이지는 `wait_seconds`를 사용하세요.
2. 극단적인 페이지는 안티봇 휴리스틱에 걸립니다. 내용이 거의 없고 스크립트 태그만 많은 페이지는 Crawl4ai의 안티봇 감지기에 의해 `Blocked by anti-bot protection: Structural: no_content_elements, script_heavy_shell`로 `success=False` 처리됩니다. 실제 서비스 페이지에서는 드물지만, 테스트는 기본적인 정적 콘텐츠(내비게이션 바, 문단 등)를 포함한 페이지에서 진행하는 것이 좋습니다.
