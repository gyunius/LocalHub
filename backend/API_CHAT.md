# LocalHub — Chat API 사용 문서

## 개요
* **목적**: 프론트엔드가 백엔드 챗봇(모의) API를 호출하여 자연어 질의에 대한 응답과 관련 POI(검색 결과)를 받도록 함.
* **엔드포인트 구현 참조**: `main.py` (mock 동작)

---

## POST /api/chat

* **설명**: 사용자 메시지를 받아 챗봇 응답(`reply`)과 관련 POI 목록(`sources`) 반환. 현재는 mock 응답이며, FTS 결과에 따라 `sources`가 비어있을 수 있음.

### Request (JSON)
| 필드명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :--- | :---: | :---: | :--- |
| `message` | string | **필수** | - | 사용자 입력 (최대 2000자) |
| `session_id` | string | 선택 | - | 클라이언트 세션 id (있으면 echo됨) |
| `user_id` | string | 선택 | - | 사용자 식별 id |
| `context` | array\|object | 선택 | - | 이전 대화 이력 |
| `bbox` | string | 선택 | - | `"minLng,minLat,maxLng,maxLat"` (검색 필터 영역) |
| `top_k` | integer | 선택 | `5` | 반환할 POI 개수 (서버 제한 상한 50) |
| `use_search` | boolean | 선택 | `true` | POI 검색 포함 여부 |

### Response (200 OK)
```json
{
  "id": "string (응답 고유 ID)",
  "reply": "string (챗봇 텍스트 응답)",
  "sources": [
    {
      "contentid": "string/integer",
      "title": "string (장소명)",
      "addr1": "string (주소)",
      "mapx": "double (경도, Lng)",
      "mapy": "double (위도, Lat)",
      "score": "double (검색 유사도 점수, Optional)"
    }
  ],
  "session_id": "string (echo 된 세션 id)",
  "model_meta": {
    "mock": true
  }
}
```

### 오류 (Errors)
* **400 Bad Request**: 필수 필드 누락(예: `message`) 또는 잘못된 형식
* **429 Too Many Requests**: 레이트리밋 (추후 적용 예정)
* **500 Internal Server Error**: 내부 서버 오류

---

## 빠른 예제 (git-bash / curl)

**성공 케이스 (간단 텍스트 질의):**
```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "경복궁 근처 맛집 추천해줘", "session_id": "test-session-123"}'
```

* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) 에서 `POST /api/chat` 직접 테스트 가능

---

## FTS / POI 데이터 준비

현재 `sources`가 빈 배열로 반환되면 DB 또는 FTS 인덱스에 POI 데이터가 없는 상태입니다.

### 데이터 로드 / FTS 생성 방법 (backend 폴더에서 실행)

#### 1. 전체 마이그레이션 + 데이터 로드
```bash
python manage.py migrate
python manage.py loaddata tour_spots.json
```

#### 2. 빠른 FTS 생성 (스크립트) — 파일: `fts_setup.py`
```bash
python fts_setup.py
```

#### 3. 검증 (간단 count 확인)
```bash
# SQLite DB에 직접 접속하여 데이터 건수 확인 예시 (Django default db.sqlite3 기준)
sqlite3 db.sqlite3 "SELECT count(*) FROM tour_spots_fts;"
```

---

## 프론트 통합 권장 사항
1. **Header 설정**: 항상 `Content-Type: application/json` 헤더를 포함하여 요청을 전송해야 합니다.
2. **예외 처리**: `sources`가 빈 배열(`[]`)로 올 때 UI 상에서 "검색 결과 없음" 또는 지도의 마커를 초기화하는 예외 처리가 필요합니다.
3. **세션 유지**: `session_id`를 프론트에서 임의 생성(UUID 등)하여 앱 유지 시간 동안 지속적으로 보내주면, 향후 백엔드에서 대화 컨텍스트(이전 대화 기억) 연동 시 그대로 활용할 수 있어 매우 유용합니다.
4. **보안/운영**: 실 운영 환경 배포 시에는 CORS 도메인 허용 범위 제한 및 클라이언트당 요청 레이트리밋 설정을 적용하는 것을 강력히 권장합니다.

---

## 테스트 체크리스트 (개발자용)
* [ ] [http://localhost:8000/docs](http://localhost:8000/docs) 에서 `POST /api/chat` 호출 및 정상 응답 확인
* [ ] FTS/POI에 데이터가 정상적으로 채워졌을 때 `sources` 배열 안에 적절한 장소 리스트가 매핑되어 오는지 확인
* [ ] 필수 값이 없거나 형식이 깨졌을 때의 에러(400/500) 케이스에 대해 프론트엔드가 앱 내에서 충돌 없이 에러 메시지를 띄우는지 검증
