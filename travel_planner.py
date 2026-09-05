"""travel_planner.py — 메인 진입점 (CLI + 파이프라인 오케스트레이션)

실행:
    python travel_planner.py --date "YYYY-MM-DD"
    python travel_planner.py --date "YYYY-MM-DD" --no-cache   # 캐시 무시

파이프라인:
    0. CLI 파싱 + 날짜 검증 + 키 로드
    1. LLM 1차 추천 (JSON, 복수 지역)
    2. 지역별 맛집 검색 (루프)
    3. LLM 최종 리포트(Markdown)
    4. results/ 저장

[보너스] 복수 지역 추천 + 결과 캐싱 포함.
"""

import os
import sys
import json
import argparse
from datetime import datetime

from dotenv import load_dotenv

import llm_client
import place_client
import report as report_mod

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = "results"
API_ENV_FILE = os.path.join(BASE_DIR, "API.env")
FALLBACK_ENV_FILE = os.path.join(BASE_DIR, ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="국내 여행 추천 프로그램 (LLM + 지도 API)"
    )
    parser.add_argument(
        "--date", required=True, help='여행 날짜 (형식: YYYY-MM-DD)'
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="같은 날짜의 캐시가 있어도 API를 다시 호출한다"
    )
    return parser.parse_args()


def validate_date(date_str: str) -> str:
    """YYYY-MM-DD 형식 검증. 실패 시 사용법 출력 후 종료."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        print('날짜 형식 오류. 사용법: --date "YYYY-MM-DD"')
        sys.exit(1)


def load_keys() -> None:
    """API.env(우선) 또는 .env/환경변수에서 API 키를 로드한다."""
    if os.path.exists(API_ENV_FILE):
        load_dotenv(API_ENV_FILE)
    elif os.path.exists(FALLBACK_ENV_FILE):
        load_dotenv(FALLBACK_ENV_FILE)

    missing = [
        key for key in ("GEMINI_API_KEY", "KAKAO_REST_API_KEY")
        if not os.getenv(key)
    ]
    if missing:
        print(f"[오류] API 키 미설정: {', '.join(missing)}")
        print("설정 방법:")
        print("  프로젝트 루트의 API.env 파일에 아래 항목을 작성하세요.")
        print("  GEMINI_API_KEY=YOUR_KEY")
        print("  KAKAO_REST_API_KEY=YOUR_KEY")
        print("  (기존 .env 또는 셸 환경변수도 계속 지원합니다.)")
        sys.exit(1)


def raw_json_path(date: str) -> str:
    return os.path.join(RESULTS_DIR, f"{date}_raw.json")


def save_raw(date: str, rec: dict, restaurants_by_city: dict, errors: list) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = raw_json_path(date)
    data = {
        "date": date,
        "recommendation": rec,
        "restaurants_by_city": restaurants_by_city,
        "errors": errors,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_cache(date: str):
    """캐시(raw.json)가 있으면 (rec, restaurants_by_city, errors)를 반환, 없으면 None."""
    path = raw_json_path(date)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return (
        data["recommendation"],
        data.get("restaurants_by_city", {}),
        data.get("errors", []),
    )


def main() -> None:
    args = parse_args()
    date = validate_date(args.date)
    load_keys()

    errors: list = []

    cache = None if args.no_cache else load_cache(date)
    if cache:
        print(f"[캐시] {raw_json_path(date)} 사용 → API 호출 건너뜀")
        rec, restaurants_by_city, errors = cache
    else:
        print("[1/3] 1차 추천 생성 중(LLM)...")
        try:
            rec = llm_client.get_recommendation(date, errors)
        except Exception as e:
            print(f"  - 오류: 1차 추천 생성 실패 → 종료 ({e})")
            sys.exit(1)
        cities = rec["recommended_cities"]
        print(f"  - recommended_cities: {cities}")

        print("[2/3] 맛집 검색 중(지도/장소 API)...")
        restaurants_by_city: dict = {}
        for city in cities:
            found = place_client.search_restaurants(city, errors, size=5)
            restaurants_by_city[city] = found
            if found:
                print(f"  - {city}: 맛집 {len(found)}곳 검색 완료")
            else:
                print(f"  - {city}: 맛집 0건 → '데이터 없음' 처리하고 계속 진행")

        save_raw(date, rec, restaurants_by_city, errors)

    print("[3/3] 최종 리포트 생성 중(LLM)...")
    markdown = report_mod.build_report(date, rec, restaurants_by_city, errors)
    md_path = report_mod.save_report(date, markdown, RESULTS_DIR)
    save_raw(date, rec, restaurants_by_city, errors)
    print("  - 리포트 생성 완료")

    print(f"\n완료! {md_path} 를 확인하세요.")


if __name__ == "__main__":
    main()
