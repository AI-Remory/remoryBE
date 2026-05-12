# 08. Deployment

## 목차

- [기준 환경](#기준-환경)
- [서버 준비](#서버-준비)
- [MySQL](#mysql)
- [프로젝트 배포](#프로젝트-배포)
- [.env 검증](#env-검증)
- [Alembic](#alembic)
- [systemd](#systemd)
- [Nginx](#nginx)
- [배포 체크리스트](#배포-체크리스트)
- [자주 발생한 오류](#자주-발생한-오류)

## 기준 환경

| 항목 | 기준 |
| --- | --- |
| OS | Ubuntu 계열 서버 |
| Python | 3.12 권장 |
| App | FastAPI `app.main:app` |
| DB | MySQL |
| Process | systemd + uvicorn |
| Reverse proxy | Nginx |

## 서버 준비

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mysql-client nginx git
```

프로젝트를 배포할 계정과 디렉터리를 준비한다.

```bash
sudo mkdir -p /opt/remory/backend
sudo chown -R $USER:$USER /opt/remory
```

## MySQL

```sql
CREATE DATABASE remory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'remory'@'%' IDENTIFIED BY 'strong-password';
GRANT ALL PRIVILEGES ON remory_db.* TO 'remory'@'%';
FLUSH PRIVILEGES;
```

운영 `.env`의 `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`와 일치해야 한다.

## 프로젝트 배포

```bash
cd /opt/remory/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p uploads/images uploads/voices uploads/photo_memories uploads/verifications uploads/chat_audio uploads/chat_tts
```

운영 `.env`에서 최소한 다음은 반드시 변경한다.

| 변수 | 운영 기준 |
| --- | --- |
| `DEBUG` | `False` |
| `ENVIRONMENT` | `production` 또는 `staging` |
| `MYSQL_*` | 실제 DB 접속 정보 |
| `SECRET_KEY` | 긴 난수 문자열 |
| `CORS_ORIGINS` | 실제 frontend origin |
| `UPLOAD_DIR` | 서버 프로세스가 쓰기 가능한 경로 |
| `GEMINI_API_KEY` | 실제 AI 기능 사용 시 설정 |

## .env 검증

Alembic과 FastAPI는 `Settings`를 import한다. `.env`에 `app/core/settings.py::Settings`가 모르는 키가 있으면 `pydantic_settings ValidationError: Extra inputs are not permitted`가 발생한다.

배포 전에 반드시 실행한다.

```bash
grep -E "^[A-Z_]+=" .env.example | cut -d= -f1 | sort > /tmp/env_example_keys.txt
grep -E "^[A-Z_]+=" .env | cut -d= -f1 | sort > /tmp/env_keys.txt
comm -23 /tmp/env_example_keys.txt /tmp/env_keys.txt
comm -13 /tmp/env_example_keys.txt /tmp/env_keys.txt
```

첫 번째 출력은 `.env`에 빠진 키다. 두 번째 출력은 `.env`에만 있는 키다. 두 번째 출력에 `RATE_LIMIT_PER_MINUTE_DEFAULT`, `RATE_LIMIT_PER_MINUTE_VOICE` 같은 값이 있으면 현재 코드가 허용하지 않으므로 제거한다.

현재 허용되는 rate limit 키는 `RATE_LIMIT_REQUESTS_PER_MINUTE_DEFAULT`, `RATE_LIMIT_REQUESTS_PER_MINUTE_VOICE`다.

## Alembic

```bash
source .venv/bin/activate
alembic current
alembic upgrade head
```

배포 중 새 migration을 만들지 않는다. schema 변경이 필요한 작업은 별도 개발/리뷰 후 `migrations/versions`에 revision을 추가한다.

## systemd

`/etc/systemd/system/remory-backend.service` 예시:

```ini
[Unit]
Description=Remory Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/remory/backend
Environment="PATH=/opt/remory/backend/.venv/bin"
ExecStart=/opt/remory/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable remory-backend
sudo systemctl restart remory-backend
sudo systemctl status remory-backend
```

## Nginx

```nginx
server {
    listen 80;
    server_name api.example.com;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/v1/ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600;
    }
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 배포 체크리스트

- `.env.example`과 `.env` 키 차이 확인
- `DEBUG=False`
- `SECRET_KEY` 운영용 난수로 교체
- `CORS_ORIGINS`에 실제 frontend origin만 설정
- `uploads/*` 디렉터리 생성 및 쓰기 권한 확인
- `alembic current`, `alembic upgrade head` 성공
- `curl http://127.0.0.1:8000/health` 성공
- Nginx WebSocket upgrade 설정 확인

## 자주 발생한 오류

### pydantic Settings ValidationError

원인: `.env`에 `Settings`에 없는 키가 있다.

해결: [.env 검증](#env-검증)의 `comm -13` 출력 키를 `.env`에서 제거한다.

### Alembic DB 접속 실패

`MYSQL_*` 값, DB 계정 권한, 방화벽, MySQL bind address를 확인한다.

### systemd 서비스 실패

```bash
journalctl -u remory-backend -n 100 --no-pager
```

`WorkingDirectory`, venv 경로, `.env` 위치, 파일 권한을 확인한다.

### 413 Request Entity Too Large

Nginx `client_max_body_size`와 `MAX_UPLOAD_SIZE`를 함께 확인한다.

### WebSocket 연결 실패

Nginx `Upgrade`, `Connection`, `proxy_http_version 1.1` 설정과 access token query parameter를 확인한다.
