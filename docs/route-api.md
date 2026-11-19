# 경로 API

`GET /api/route`에 `start_x`, `start_y`, `end_x`, `end_y` 좌표를 전달합니다. `mode`는 `walk`(기본값), `transit`, `car` 중 선택합니다. 서버는 각각 카카오맵 도보·대중교통 API와 카카오모빌리티 자동차 길찾기 API의 JSON 응답을 반환합니다. REST 키가 없으면 503, 잘못된 좌표나 이동 수단은 400, 외부 API 연결 실패는 502를 반환합니다.
