# 편의시설 정정 요청 API

## POST /api/facility-corrections

`{"place_name":"장소명","address":"주소","lat":35.7739,"lon":128.4309,"content":"정정 내용"}`을 JSON으로 전달합니다. 장소명과 내용은 필수이며 주소는 빈 문자열을 허용합니다. 위도와 경도는 한국 범위여야 합니다. 성공 시 201, 잘못된 입력은 400을 반환합니다. 서버의 SQLite `facility_corrections` 테이블에 저장되며 공공데이터에 자동 반영되지 않습니다. 관리자에게 공개 조회 API는 제공하지 않으며 SQLite에서 직접 검토합니다.
