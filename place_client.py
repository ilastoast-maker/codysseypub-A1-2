"""place_client.py — 지도/장소 검색 API 호출 (Kakao Local 기준)

- search_restaurants(city, errors, size=5) : 맛집 리스트 반환
- HTTP GET, 인증 헤더에 키를 실어 요청한다 (Authorization: KakaoAK {KEY}).
- 인증 실패(401/403) / 네트워크 / 0건을 각각 구분해 errors에 기록하고,
  예외를 밖으로 던지지 않고 빈 리스트를 반환한다(파이프라인 중단 방지).

Naver Local Search로 교체 시 URL/헤더(X-Naver-Client-Id/Secret)와
응답 필드 매핑만 바꾸면 된다.
"""

import os
import requests

import errors as E

KAKAO_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def _map_item(doc: dict) -> dict:
    """Kakao 응답 아이템을 표준 맛집 스키마로 변환한다."""
    return {
        "name": doc.get("place_name", ""),
        "address": doc.get("road_address_name") or doc.get("address_name", ""),
        "category": doc.get("category_name", ""),
        "url": doc.get("place_url", ""),
        "x": float(doc["x"]) if doc.get("x") else None,
        "y": float(doc["y"]) if doc.get("y") else None,
    }


def search_restaurants(city: str, errors: list, size: int = 5) -> list:
    """도시 기준 맛집 N곳을 검색해 표준 스키마 리스트로 반환한다."""
    api_key = os.getenv("KAKAO_REST_API_KEY")
    if not api_key:
        E.add_error(errors, "place_search", E.AUTH_ERROR, "KAKAO_REST_API_KEY 미설정")
        return []

    query = f"{city} 맛집"
    try:
        resp = requests.get(
            KAKAO_URL,
            headers={"Authorization": f"KakaoAK {api_key}"},
            params={"query": query, "size": size},
            timeout=15,
        )
    except requests.RequestException as e:
        E.add_error(errors, "place_search", E.NETWORK_ERROR, f"{e}")
        return []

    if resp.status_code in (401, 403):
        E.add_error(errors, "place_search", E.AUTH_ERROR, f"HTTP {resp.status_code}")
        return []
    if resp.status_code == 429:
        E.add_error(errors, "place_search", E.QUOTA_ERROR, "HTTP 429")
        return []
    if resp.status_code != 200:
        E.add_error(errors, "place_search", E.NETWORK_ERROR, f"HTTP {resp.status_code}")
        return []

    docs = resp.json().get("documents", [])
    if not docs:
        E.add_error(errors, "place_search", E.EMPTY_RESULT, f"0 results for query={query}")
        return []

    return [_map_item(d) for d in docs]
