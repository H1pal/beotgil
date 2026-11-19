# 시설 편의정보 API

`GET /api/facility?name=시설명&lat=위도&lon=경도`는 공공데이터 시설 목록과 편의시설 상세를 조회합니다. 정확한 이름과 50m 이내 좌표가 일치하는 시설이 하나일 때만 등록 정보를 반환하며, 일치하지 않거나 여러 개이면 `status: unknown`을 반환합니다. 인증키는 서버 환경변수 `BEOTGIL_PUBLIC_DATA_KEY`로 설정합니다. 응답의 `facilities`는 제공기관에 등록된 정보로, 휠체어 이용 가능 여부를 보장하지 않습니다.
