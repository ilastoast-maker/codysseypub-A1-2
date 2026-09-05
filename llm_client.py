"""llm_client.py — LLM API 호출, JSON 파싱, 재시도 로직

- get_recommendation(date)         : 1차 추천 JSON 생성/파싱 (파싱 실패 시 1회 재시도)
- generate_report_body(...)        : 최종 Markdown 리포트 생성
- HTTP POST 방식으로 LLM API를 호출한다.

기본 구현은 Google Gemini(REST) 기준이며, OpenAI 계열로 교체 가능하다.

[보너스] 1차 추천은 recommended_cities(2~3개) 배열로 받으며,
단일 도시만 필요할 경우 첫 번째 원소를 사용하면 된다.
"""

import os
import json
import re
import requests

import errors as E

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

REQUIRED_KEYS = ["recommended_cities", "weather", "events", "reason"]


def _call_llm(prompt: str) -> str:
    """LLM에 프롬프트를 POST하고 응답 텍스트를 반환한다."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 미설정")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    resp = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json"},
        params={"key": api_key},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _extract_json(text: str) -> dict:
    """응답 텍스트에서 JSON 블록을 안전하게 추출/파싱한다."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("JSON 블록을 찾을 수 없음")
    return json.loads(text[start:end + 1])


def _normalize(obj: dict) -> dict:
    """스키마를 보정한다. recommended_city(단일)로 와도 배열로 승격."""
    if "recommended_cities" not in obj and "recommended_city" in obj:
        obj["recommended_cities"] = [obj["recommended_city"]]
    return obj


def _has_required_keys(obj: dict) -> bool:
    if not all(k in obj for k in REQUIRED_KEYS):
        return False
    return isinstance(obj["recommended_cities"], list) and len(obj["recommended_cities"]) >= 1


def _prompt_recommendation(date: str) -> str:
    return f"""당신은 국내 여행 추천 전문가입니다.
여행 날짜: {date}
이 시기에 여행하기 좋은 국내 도시 2~3곳을 추천하고, 아래 JSON만 출력하세요.
설명 문장이나 코드펜스 없이 순수 JSON만 출력합니다.

{{
  "recommended_cities": ["도시명 2~3개 (예: 제주, 강릉)"],
  "weather": "해당 시기 전반적 날씨 요약",
  "events": ["행사/축제 후보 1~3개"],
  "reason": "추천 근거 2~4문장"
}}"""


def _prompt_recommendation_retry(date: str) -> str:
    return f"""여행 날짜 {date} 에 대해 아래 4개 키만 가진 JSON 하나만 출력하세요.
다른 텍스트/코드펜스 금지.
키: recommended_cities(array of string, 2~3개), weather(string), events(array of string), reason(string)"""


def get_recommendation(date: str, errors: list) -> dict:
    """1차 추천 JSON을 반환한다. 파싱 실패 시 1회 재시도."""
    try:
        raw = _call_llm(_prompt_recommendation(date))
        obj = _normalize(_extract_json(raw))
        if _has_required_keys(obj):
            return obj
        raise ValueError("필수 키 누락")
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        E.add_error(errors, "llm_recommend", E.LLM_PARSE_ERROR, f"1차 파싱 실패: {e}")

    raw = _call_llm(_prompt_recommendation_retry(date))
    obj = _normalize(_extract_json(raw))
    if not _has_required_keys(obj):
        raise RuntimeError("LLM 1차 추천 JSON 파싱 재시도 실패")
    return obj


def _prompt_report(date: str, recommendation: dict, restaurants_by_city: dict) -> str:
    return f"""아래 데이터를 바탕으로 한국어 여행 리포트를 Markdown으로 작성하세요.
반드시 다음 섹션을 포함: 추천 지역, 추천 이유, 날씨 요약, 행사/축제, 맛집 추천(지역별로 정리), 1일 일정 제안(오전/오후/저녁).
맛집이 0건인 지역은 '데이터 없음 (장소 검색 결과 0건)'으로 표기하세요.

날짜: {date}
1차 추천 JSON:
{json.dumps(recommendation, ensure_ascii=False, indent=2)}

지역별 맛집 목록:
{json.dumps(restaurants_by_city, ensure_ascii=False, indent=2)}
"""


def generate_report_body(date: str, recommendation: dict, restaurants_by_city: dict) -> str:
    """LLM으로 리포트 본문(Markdown)을 생성해 반환한다."""
    return _call_llm(_prompt_report(date, recommendation, restaurants_by_city))
