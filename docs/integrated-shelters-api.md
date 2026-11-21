# 통합대피소 API

## GET /api/integrated-shelters?type=3

`BEOTGIL_INTEGRATED_SAFETY_KEY`로 행정안전부 통합대피소 API를 조회합니다. `type`은 한파 1, 무더위 2, 지진 옥외 3, 지진해일 4입니다. 구지읍 또는 구지면으로 주소가 등록된 달성군 장소만 반환합니다. 응답은 `shelters` 배열과 `source`, `area`를 포함합니다. 항목은 `id`, `name`, `address`, `lat`, `lon`, `type`을 포함합니다. 키 누락 503, 외부 오류 502, 잘못된 종류 400입니다. 자료 출처: https://www.safetydata.go.kr/disaster-data/view?dataSn=1346
