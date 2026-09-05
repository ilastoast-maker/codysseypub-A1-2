"""errors.py — 오류 수집/기록 유틸

프로그램 전체에서 공유하는 errors 리스트에 표준 형식으로 오류를 추가한다.
표준 형식: {"step": str, "type": str, "message": str}
JSON 저장과 리포트 생성 양쪽에서 동일한 구조를 재사용한다.
"""

# 오류 타입 상수 (에러 처리 정책과 1:1 매핑)
LLM_PARSE_ERROR = "LLM_PARSE_ERROR"
AUTH_ERROR = "AUTH_ERROR"
NETWORK_ERROR = "NETWORK_ERROR"
QUOTA_ERROR = "QUOTA_ERROR"
EMPTY_RESULT = "EMPTY_RESULT"


def add_error(errors: list, step: str, err_type: str, message: str) -> None:
    """공유 errors 리스트에 표준 형식으로 오류를 추가한다."""
    errors.append({
        "step": step,
        "type": err_type,
        "message": str(message),
    })
