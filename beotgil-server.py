import json
import os
import ssl
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen

class BeotgilHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/":
            self.path = "/index.html"
            return super().do_GET()
        if url.path != "/api/route":
            return super().do_GET()
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
        request = Request("https://dapi.kakao.com/v2/routing/walk?" + urlencode(values),
                          headers={"Authorization": "KakaoAK " + key})
        try:
            with urlopen(request, timeout=15, context=ssl.create_default_context(cafile="/etc/ssl/cert.pem")) as response:
                data = json.load(response)
        except HTTPError as error:
            return self.send_json(502, {"message": "카카오 경로 API 요청에 실패했습니다. REST API 키와 이용 설정을 확인해 주세요.", "upstream_status": error.code})
        except (URLError, TimeoutError, ValueError):
            return self.send_json(502, {"message": "카카오 경로 API에 연결하지 못했습니다."})
        self.send_json(200, data)

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
    ThreadingHTTPServer(("127.0.0.1", 8081), BeotgilHandler).serve_forever()
