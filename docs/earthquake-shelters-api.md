# 지진 옥외 대피장소 API

## GET /api/earthquake-shelters

서버의 `BEOTGIL_SAFETY_DATA_KEY`를 사용해 행정안전부 지진옥외대피장소 API를 조회하고 달성군 자료의 이름, 주소, 위도, 경도를 반환합니다. 응답: `{"shelters":[{"id":"1","name":"장소","address":"주소","lat":35.66,"lon":128.41}],"source":"행정안전부 지진옥외대피장소"}`. 서비스키 미설정 시 503, 외부 API 오류 시 502입니다. 이용조건과 데이터 출처는 [재난안전데이터 공유플랫폼](https://www.safetydata.go.kr/disaster-data/view?dataSn=1339)을 참고하세요. 이 데이터는 지진 초기 옥외 대피장소이며 운영 상태나 휠체어 접근성을 보장하지 않습니다.
