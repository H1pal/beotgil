# 건의 사항 API

## GET /api/suggestions

최근 건의 사항 최대 50건을 최신순으로 반환합니다. 응답은 `{"suggestions":[{"content":"내용","created_at":"UTC 시각"}]}` 형식입니다.

## POST /api/suggestions

JSON `{"content":"내용"}`을 전달합니다. 내용은 공백을 제외하고 1~1000자여야 합니다. 성공 시 HTTP 201을 반환하고 잘못된 입력에는 HTTP 400을 반환합니다. 건의 사항은 서버 로컬 SQLite 파일에 저장됩니다.
