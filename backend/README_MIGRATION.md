Quick start (backend 폴더에서):

1) 가상환경/의존성
python -m venv venv
# Windows PowerShell
venv\\Scripts\\Activate.ps1
pip install -r requirements.txt

2) .env 설정
cp .env.example .env
(필요하면 경로 수정)

3) dry-run(테스트)
python migrate.py --dry-run

4) 소량 테스트 (파일당 최대 10개)
python migrate.py --sample 10

5) 전체 마이그레이션
python migrate.py

6) API 실행
uvicorn main:app --reload --port 8000