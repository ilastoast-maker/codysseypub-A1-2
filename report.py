"""report.py — 최종 Markdown 리포트 생성/저장

- build_report(...)  : 1차 JSON + 지역별 맛집 + errors → Markdown 문자열
- save_report(...)   : results/{date}_travel_plan.md 로 저장

LLM 본문 생성이 실패해도 로컬 폴백 템플릿으로 리포트를 완성한다.
[보너스] 맛집은 지역(도시)별로 정리한다.
"""

import os

import llm_client


def _restaurants_md(restaurants: list) -> str:
    if not restaurants:
        return "- 데이터 없음 (장소 검색 결과 0건)"
    lines = []
    for r in restaurants:
        line = f"- **{r['name']}** ({r.get('category', '')})\n  - 주소: {r.get('address', '')}"
        if r.get("url"):
            line += f"\n  - 링크: {r['url']}"
        lines.append(line)
    return "\n".join(lines)


def _errors_md(errors: list) -> str:
    if not errors:
        return "- 없음"
    return "\n".join(
        f"- [{e['step']}] {e['type']}: {e['message']}" for e in errors
    )


def _fallback_body(date: str, rec: dict, restaurants_by_city: dict) -> str:
    """LLM 리포트 생성이 실패했을 때 사용하는 로컬 템플릿."""
    events = "\n".join(f"- {ev}" for ev in rec.get("events", [])) or "- 정보 없음"
    cities = rec.get("recommended_cities", [])

    rest_sections = []
    for city in cities:
        rest_sections.append(f"### {city}\n{_restaurants_md(restaurants_by_city.get(city, []))}")
    rest_md = "\n\n".join(rest_sections) or "- 데이터 없음"

    return f"""# {date} 국내 여행 추천 리포트

## 추천 지역
{', '.join(cities)}

## 추천 이유
{rec.get('reason', '')}

## 날씨 요약
{rec.get('weather', '')}

## 행사/축제
{events}

## 맛집 추천
{rest_md}

## 1일 일정 제안
- 오전: 추천 지역 대표 명소 방문
- 오후: 인근 관광 + 맛집 점심
- 저녁: 지역 야경/휴식
"""


def build_report(date: str, rec: dict, restaurants_by_city: dict, errors: list) -> str:
    """최종 리포트 Markdown 문자열을 생성한다."""
    try:
        body = llm_client.generate_report_body(date, rec, restaurants_by_city)
    except Exception as e:
        from errors import add_error
        add_error(errors, "llm_report", "NETWORK_ERROR", f"리포트 생성 실패, 폴백 사용: {e}")
        body = _fallback_body(date, rec, restaurants_by_city)

    return f"{body.rstrip()}\n\n## 오류 요약(errors)\n{_errors_md(errors)}\n"


def save_report(date: str, markdown: str, results_dir: str = "results") -> str:
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, f"{date}_travel_plan.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return path
