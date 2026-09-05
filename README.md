# 국내 여행 추천 프로그램 (Travel Planner CLI)

LLM API와 지도(장소 검색) API를 조합하여, 사용자가 입력한 여행 날짜에 맞는 국내 여행지를 추천하고 맛집을 검색한 뒤 최종 여행 리포트를 자동 생성하는 CLI 기반 Python 프로그램입니다.

> 저장소: `ilastoast-maker/codysseypub`  
> 브랜치: `09a2`  
> 과제 폴더: `A1-2`

---

## 1. 프로그램 개요

- 사용자가 CLI로 여행 날짜(`--date "YYYY-MM-DD"`)를 입력합니다.
- Google Gemini API가 여행하기 좋은 국내 도시 2~3곳을 `recommended_cities` 배열로 추천합니다.
- Kakao Local API가 각 추천 도시의 맛집을 검색해 `restaurants_by_city` 딕셔너리로 저장합니다.
- Gemini API가 추천 정보와 맛집 정보를 종합하여 Markdown 여행 리포트를 생성합니다.
- 외부 API 오류는 `errors` 리스트에 기록하고 최종 JSON/리포트에 반영합니다.

사용 API:

| 구분 | 서비스 |
|---|---|
| LLM API | Google Gemini |
| 지도/장소 API | Kakao Local |

---

## 2. 파이프라인

```text
[사용자 입력]
python travel_planner.py --date "2026-03-15"
        ↓
[입력 검증 + API 키 로드]
        ↓
[Gemini 1차 추천]
{ recommended_cities[], weather, events[], reason }
        ↓
[Kakao 장소 검색]
restaurants_by_city = {
  "제주": [...],
  "강릉": [...]
}
        ↓
[Gemini 최종 리포트]
        ↓
results/{date}_raw.json
results/{date}_travel_plan.md
```

---

## 3. 프로젝트 구조

```text
codysseypub/
└── A1-2/
    ├── travel_planner.py      # 메인 실행 및 파이프라인
    ├── llm_client.py          # Gemini API 호출/JSON 파싱/재시도
    ├── place_client.py        # Kakao Local 장소 검색
    ├── report.py              # Markdown 리포트 생성/저장
    ├── errors.py              # 오류 기록 유틸
    ├── requirements.txt       # 의존성
    ├── API.env.example        # API 키 변수명 예시(실제 키 없음)
    ├── .gitignore             # API.env/.env/results 등 제외
    └── README.md
```

`results/` 폴더는 프로그램 실행 시 자동 생성됩니다.

---

## 4. 설치 및 실행

### 저장소 클론

```bash
git clone -b 09a2 https://github.com/ilastoast-maker/codysseypub.git
cd codysseypub/A1-2
```

### 의존성 설치

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
```

`requirements.txt`:

```text
requests
python-dotenv
```

### 실행

```bash
python travel_planner.py --date "2026-03-15"
```

캐시를 무시하고 API를 다시 호출하려면:

```bash
python travel_planner.py --date "2026-03-15" --no-cache
```

---

## 5. API 키 설정

이 프로젝트는 `travel_planner.py`와 같은 `A1-2` 폴더의 `API.env`를 우선 읽습니다. `API.env`가 없으면 기존 `.env`를 확인하며, 셸 환경변수도 사용할 수 있습니다.

`API.env.example`을 복사합니다.

```bash
cp API.env.example API.env
```

그 다음 실제 키를 입력합니다.

```env
GEMINI_API_KEY=여기에_본인_Gemini_API_KEY
KAKAO_REST_API_KEY=여기에_본인_Kakao_REST_API_KEY
```

> `API.env`와 `.env`에는 실제 비밀키가 들어가므로 GitHub에 업로드하지 않습니다. `.gitignore`에 두 파일이 모두 등록되어 있습니다.

---

## 6. 데이터 구조

### Gemini 1차 추천

```json
{
  "recommended_cities": ["제주", "강릉"],
  "weather": "날씨 요약",
  "events": ["행사 후보"],
  "reason": "추천 이유"
}
```

`llm_client.py`는 `recommended_city` 단일 값으로 응답이 와도 `recommended_cities` 배열로 보정합니다.

### 지역별 맛집 결과

```json
{
  "restaurants_by_city": {
    "제주": [
      {
        "name": "맛집 예시",
        "address": "주소",
        "category": "음식점 카테고리",
        "url": "장소 URL",
        "x": 0.0,
        "y": 0.0
      }
    ],
    "강릉": []
  }
}
```

각 도시의 검색 결과가 0건이어도 빈 리스트(`[]`)로 유지하고 전체 파이프라인은 계속 진행합니다.

---

## 7. 주요 기능

### `travel_planner.py`
- CLI `--date` 입력 및 `YYYY-MM-DD` 형식 검증
- `API.env` → `.env` → 환경변수 순으로 API 키 사용
- Gemini 추천 → Kakao 맛집 검색 → 리포트 생성 흐름 제어
- 날짜별 raw JSON 캐싱

### `llm_client.py`
- Gemini REST API HTTP POST 호출
- JSON 응답 파싱
- 필수 키: `recommended_cities`, `weather`, `events`, `reason`
- 파싱 실패 시 1회 재시도
- 최종 Markdown 리포트 본문 생성

### `place_client.py`
- Kakao Local 키워드 검색 API HTTP GET 호출
- 헤더: `Authorization: KakaoAK {KEY}`
- 인증 오류(401/403), 쿼터(429), 네트워크 오류, 0건 결과 구분

### `report.py`
- LLM 리포트 생성 실패 시 로컬 폴백 리포트 생성
- 맛집을 도시별 섹션으로 구성
- 마지막에 오류 요약(`errors`) 추가

### `errors.py`

```json
{
  "step": "place_search",
  "type": "AUTH_ERROR",
  "message": "HTTP 401"
}
```

오류 타입:
- `LLM_PARSE_ERROR`
- `AUTH_ERROR`
- `NETWORK_ERROR`
- `QUOTA_ERROR`
- `EMPTY_RESULT`

---

## 8. 결과 저장

실행 후 `results/` 폴더에 다음 파일이 생성됩니다.

```text
results/
├── 2026-03-15_raw.json
└── 2026-03-15_travel_plan.md
```

raw JSON 핵심 구조:

```json
{
  "date": "2026-03-15",
  "recommendation": {
    "recommended_cities": ["제주", "강릉"],
    "weather": "...",
    "events": ["..."],
    "reason": "..."
  },
  "restaurants_by_city": {
    "제주": [],
    "강릉": []
  },
  "errors": []
}
```

최종 Markdown 리포트에는 다음 섹션이 포함됩니다.

```text
추천 지역
추천 이유
날씨 요약
행사/축제
맛집 추천
1일 일정 제안
오류 요약(errors)
```

---

## 9. 보너스 구현

### 복수 지역 추천
기존 단일 `recommended_city` 대신 `recommended_cities` 배열을 사용하고, 모든 추천 도시를 반복하여 맛집 검색을 수행합니다.

### 결과 캐싱
같은 날짜의 `results/{date}_raw.json`이 있으면 API 호출을 건너뛰고 저장된 데이터를 재사용합니다. `--no-cache` 옵션으로 캐시를 무시할 수 있습니다.

---

## 10. 보안 주의사항

- 실제 API 키를 코드, README, 결과 JSON/Markdown에 작성하지 않습니다.
- 실제 키 파일 `API.env`와 `.env`는 저장소에 올리지 않습니다.
- 키가 외부에 노출된 경우 Google AI Studio와 Kakao Developers에서 즉시 재발급합니다.
