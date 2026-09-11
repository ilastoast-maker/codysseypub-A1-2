VENV 사용 안내

이 프로젝트는 로컬 가상환경(venv)을 사용하도록 권장합니다. 로컬 가상환경 디렉터리(`.venv/` 또는 `venv/`)는 버전 관리에서 제외되어 있습니다.

생성 및 사용 예시 (macOS/Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

가상환경 정보를 저장하거나 공유하려면 다음 중 하나를 사용하세요:

- `pip freeze > requirements.txt` — 현재 설치된 패키지 목록을 기록
- `python -m pip list --format=columns` — 로컬에서 빠르게 확인

주의: 가상환경 디렉터리 자체를 Git에 올리지 마세요(민감한 파일 포함 가능).
