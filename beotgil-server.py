import json
import os
import ssl
import sqlite3
import math
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit, unquote
from urllib.request import Request, urlopen

class BeotgilHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/api/earthquake-shelters":
            return self.getEarthquakeShelters()
        if url.path == "/api/facility":
            return self.get_facility(url.query)
        if url.path == "/api/suggestions":
            return self.get_suggestions()
        if url.path == "/":
            self.path = "/index.html"
            return super().do_GET()
        if url.path != "/api/route":
            self.send_error(404)
            return
        key = os.environ.get("BEOTGIL_KAKAO_REST_KEY")
        if not key:
            return self.send_json(503, {"message": "서버에 카카오 REST API 키가 설정되지 않았습니다."})
        params = parse_qs(url.query)
        fields = ("start_x", "start_y", "end_x", "end_y")
        try:
            values = {field: float(params[field][0]) for field in fields}
            if not all(124 <= values[field] <= 132 for field in ("start_x", "end_x")):
                raise ValueError()
            if not all(33 <= values[field] <= 39 for field in ("start_y", "end_y")):
                raise ValueError()
        except (KeyError, ValueError, IndexError):
            return self.send_json(400, {"message": "출발지와 도착지 좌표를 확인해 주세요."})
        mode = params.get("mode", ["walk"])[0]
        if mode not in ("walk", "transit", "car"):
            return self.send_json(400, {"message": "지원하지 않는 이동 수단입니다."})
        if mode == "car":
            endpoint = "https://apis-navi.kakaomobility.com/v1/directions"
            query = {"origin": f"{values['start_x']},{values['start_y']}",
                     "destination": f"{values['end_x']},{values['end_y']}", "summary": "false"}
        else:
            endpoint = "https://dapi.kakao.com/v2/routing/" + ("walk" if mode == "walk" else "publictraffic")
            query = values
        request = Request(endpoint + "?" + urlencode(query),
                          headers={"Authorization": "KakaoAK " + key})
        try:
            with urlopen(request, timeout=15, context=ssl.create_default_context(cafile="/etc/ssl/cert.pem")) as response:
                data = json.load(response)
        except HTTPError as error:
            return self.send_json(502, {"message": "카카오 경로 API 요청에 실패했습니다. REST API 키와 이용 설정을 확인해 주세요.", "upstream_status": error.code})
        except (URLError, TimeoutError, ValueError):
            return self.send_json(502, {"message": "카카오 경로 API에 연결하지 못했습니다."})
        self.send_json(200, data)

    def getEarthquakeShelters(self):
        key = os.environ.get("BEOTGIL_SAFETY_DATA_KEY")
        if not key:
            return self.send_json(503, {"message": "지진 대피장소 API 서비스키가 설정되지 않았습니다."})
        def collectRows(value):
            if isinstance(value, list):
                return [row for item in value for row in collectRows(item)]
            if isinstance(value, dict):
                if "LA" in value and "LO" in value:
                    return [value]
                return [row for item in value.values() for row in collectRows(item)]
            return []
        shelters = []
        try:
            for page in range(1, 21):
                params = {"serviceKey": key, "returnType": "json", "pageNo": page, "numOfRows": 100,
                          "arcd": "2771000000"}
                request = Request("https://www.safetydata.go.kr/V2/api/DSSP-IF-10943?" + urlencode(params))
                with urlopen(request, timeout=15, context=ssl.create_default_context(cafile="/etc/ssl/cert.pem")) as response:
                    data = json.load(response)
                header = data.get("header", {}) if isinstance(data, dict) else {}
                code = str(header.get("resultCode", ""))
                if code == "32":
                    return self.send_json(502, {"message": "재난안전데이터에 등록되지 않은 IP입니다. 서비스키 신청 내역에서 서버의 공인 IP를 확인해 주세요."})
                if code and code not in ("0", "00", "0000"):
                    return self.send_json(502, {"message": "지진 대피장소 API 인증 또는 요청을 확인해 주세요. 오류 코드: " + code})
                rows = collectRows(data)
                if not rows and page == 1:
                    raise ValueError("대피장소 응답을 확인할 수 없습니다.")
                for row in rows:
                    if not str(row.get("ARCD", "")).startswith("27710"):
                        continue
                    try:
                        lat, lon = float(row["LA"]), float(row["LO"])
                    except (ValueError, TypeError):
                        continue
                    if not (35.55 <= lat <= 36.05 and 128.30 <= lon <= 128.78):
                        continue
                    shelters.append({"id": str(row.get("ACMDFCLTY_SN", "")), "name": str(row.get("VT_ACMDFCLTY_NM", "지진 옥외 대피장소")),
                                     "address": str(row.get("RN_DTL_ADRES") or row.get("EQK_ACMDFCLTY_ADRES") or ""), "lat": lat, "lon": lon})
                if len(rows) < 100:
                    break
            else:
                return self.send_json(502, {"message": "대피장소 목록이 너무 많아 전체 목록을 확인하지 못했습니다."})
        except (HTTPError, URLError, TimeoutError, ValueError, TypeError):
            return self.send_json(502, {"message": "지진 대피장소 정보를 불러오지 못했습니다. API 키와 이용 상태를 확인해 주세요."})
        self.send_json(200, {"shelters": shelters, "source": "행정안전부 지진옥외대피장소"})

    def get_facility(self, query):
        key = os.environ.get("BEOTGIL_PUBLIC_DATA_KEY")
        if not key:
            return self.send_json(503, {"message": "공공데이터 인증키가 설정되지 않았습니다."})
        params = parse_qs(query)
        name = params.get("name", [""])[0].strip()
        try:
            lat = float(params["lat"][0])
            lon = float(params["lon"][0])
            if not name or len(name) > 100 or not (33 <= lat <= 39 and 124 <= lon <= 132):
                raise ValueError()
        except (KeyError, ValueError, IndexError):
            return self.send_json(400, {"message": "장소 이름과 좌표를 확인해 주세요."})
        endpoint = "https://apis.data.go.kr/B554287/DisabledPersonConvenientFacility/"
        def read_xml(operation, parameters):
            parameters["serviceKey"] = unquote(key)
            request = Request(endpoint + operation + "?" + urlencode(parameters))
            with urlopen(request, timeout=20, context=ssl.create_default_context(cafile="/etc/ssl/cert.pem")) as response:
                root = ET.fromstring(response.read())
            code = root.findtext(".//resultCode")
            if code not in ("0", "00", "0000"):
                raise ValueError("공공데이터 API 오류")
            return root
        try:
            root = read_xml("getDisConvFaclList", {"faclNm": name, "siDoNm": "대구광역시", "cggNm": "달성군", "numOfRows": 100, "pageNo": 1})
            def normalize(value):
                return "".join(value.split()).casefold()
            matches = []
            for item in root.findall(".//servList") + root.findall(".//item"):
                if normalize(item.findtext("faclNm", "")) != normalize(name):
                    continue
                try:
                    item_lat = float(item.findtext("faclLat", ""))
                    item_lon = float(item.findtext("faclLng", ""))
                except ValueError:
                    continue
                distance = math.hypot((item_lat - lat) * 111000, (item_lon - lon) * 111000 * math.cos(math.radians(lat)))
                if distance <= 50 and item.findtext("wfcltId"):
                    matches.append((distance, item))
            if len(matches) != 1:
                return self.send_json(200, {"status": "unknown", "message": "일치하는 시설을 확인하지 못했습니다."})
            item = matches[0][1]
            details = read_xml("getFacInfoOpenApiJpEvalInfoList", {"wfcltId": item.findtext("wfcltId")})
            info = [element.text.strip() for element in details.findall(".//evalInfo") if element.text and element.text.strip()]
            return self.send_json(200, {"status": "found" if info else "unknown", "name": item.findtext("faclNm"), "address": item.findtext("lcMnad", ""), "facilities": info})
        except (HTTPError, URLError, TimeoutError, ValueError, ET.ParseError):
            return self.send_json(502, {"message": "공공데이터 편의시설 정보를 조회하지 못했습니다. 인증키와 API 이용 상태를 확인해 주세요."})

    def do_POST(self):
        if urlsplit(self.path).path == "/api/facility-corrections":
            return self.saveFacilityCorrection()
        if urlsplit(self.path).path != "/api/suggestions":
            return self.send_error(404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 10000:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            content = data.get("content", "")
            if not isinstance(content, str) or not 1 <= len(content.strip()) <= 1000:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            return self.send_json(400, {"message": "건의 사항은 1~1000자로 입력해 주세요."})
        with sqlite3.connect(database_path) as connection:
            connection.execute("INSERT INTO suggestions (content) VALUES (?)", (content.strip(),))
        self.send_json(201, {"message": "건의 사항이 저장되었습니다."})

    def saveFacilityCorrection(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 10000:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            name, address, content = (data.get(key, "") for key in ("place_name", "address", "content"))
            if not all(isinstance(value, str) for value in (name, address, content)):
                raise ValueError()
            name, address, content = name.strip(), address.strip(), content.strip()
            lat, lon = float(data["lat"]), float(data["lon"])
            if not (1 <= len(name) <= 200 and len(address) <= 300 and 1 <= len(content) <= 1000):
                raise ValueError()
            if not (math.isfinite(lat) and math.isfinite(lon) and 33 <= lat <= 39 and 124 <= lon <= 132):
                raise ValueError()
        except (ValueError, TypeError, AttributeError, KeyError):
            return self.send_json(400, {"message": "장소와 정정 내용을 확인해 주세요."})
        with sqlite3.connect(database_path) as connection:
            connection.execute("INSERT INTO facility_corrections (place_name, address, lat, lon, content) VALUES (?, ?, ?, ?, ?)", (name, address, lat, lon, content))
        self.send_json(201, {"message": "정정 요청이 저장되었습니다."})

    def get_suggestions(self):
        with sqlite3.connect(database_path) as connection:
            rows = connection.execute("SELECT content, created_at FROM suggestions ORDER BY id DESC LIMIT 50").fetchall()
        self.send_json(200, {"suggestions": [{"content": row[0], "created_at": row[1]} for row in rows]})

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.environ.get("BEOTGIL_DATA_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "beotgil-data.sqlite3"))
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS facility_corrections (id INTEGER PRIMARY KEY, place_name TEXT NOT NULL, address TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        connection.execute("CREATE TABLE IF NOT EXISTS suggestions (id INTEGER PRIMARY KEY, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    ThreadingHTTPServer(("127.0.0.1", 8081), BeotgilHandler).serve_forever()
