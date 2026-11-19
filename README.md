# 벗길

대구 달성군의 휠체어 이용자를 위한 이동 및 대피 내비게이션 시제품입니다.

## 실행

Python 3에서 카카오 REST API 키를 환경변수 `BEOTGIL_KAKAO_REST_KEY`로 설정한 다음 `python3 beotgil-server.py`를 실행하고 `http://localhost:8081/`에 접속합니다. 카카오맵 JavaScript 키에 해당 도메인을 등록해야 합니다.

현재 경로는 카카오맵 일반 도보 경로입니다. 경사로, 계단, 단차 및 재난 위험 정보는 연결되지 않았습니다.
