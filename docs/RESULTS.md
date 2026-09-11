results/ 폴더 안내

`results/` 폴더는 `travel_planner.py` 실행 시 생성되는 출력(원시 JSON, Markdown 리포트 등)을 저장합니다.
이 저장소는 `results/`를 `.gitignore`에 등록하여 자동 생성 파일이 커밋되지 않도록 설정되어 있습니다.

만약 특정 결과만 버전 관리하고 싶다면, 해당 파일만 골라 수동으로 커밋하세요. 예:

```bash
# 예시: 특정 리포트만 추가
git add results/2026-09-11_travel_plan.md
git commit -m "Add travel plan for 2026-09-11"
git push
```

또는 자동화된 테스트 출력이나 샘플 결과를 저장하고 싶다면, `docs/samples/` 같은 별도 폴더를 만들어 커밋하세요.
