이 폴더는 `travel_planner.py` 실행 시 생성되는 출력(여행 계획 마크다운, 원시 JSON 등)을 저장합니다.

- 현재 `results/`는 버전 관리에서 제외되어 있습니다(`.gitignore`).
- 출력물을 안전하게 저장하거나 공유하려면 수동으로 커밋하거나, 민감한 정보가 포함되어 있지 않은지 확인하세요.

권장 사용법:
1. 스크립트를 실행하여 결과 파일을 생성합니다.
2. 필요하면 특정 결과 파일만 골라 커밋합니다.

예시:
```
./.venv/bin/python travel_planner.py --date "2026-09-11"
git add results/2026-09-11_travel_plan.md
git commit -m "Add travel plan for 2026-09-11"
git push
```
