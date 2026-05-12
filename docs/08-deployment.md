# 08. Deployment

## 목차

- [기준 환경](#기준-환경)
- [Vultr/Ubuntu 초기 설정](#vultrubuntu-초기-설정)
- [MySQL](#mysql)
- [프로젝트 배포](#프로젝트-배포)
- [Alembic](#alembic)
- [systemd](#systemd)
- [Nginx](#nginx)
- [CORS](#cors)
- [GitHub Actions](#github-actions)
- [배포 체크리스트](#배포-체크리스트)
- [자주 발생한 오류](#자주-발생한-오류)

## 기준 환경

- Vultr VPS
- Ubuntu 22.04 또는 24.04
- Python 3.12
- MySQL 8.x
- Nginx
- systemd
- Uvicorn

## Vultr/Ubuntu 초기 설정

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mysql-server nginx git
```

앱 사용자 생성:

```bash
sudo adduser remory
sudo usermod -aG sudo remory
```

프로젝트 위치 예시:

```text
/srv/remory/backend
```

## MySQL

```bash
sudo systemctl enable mysql
sudo systemctl start mysql
sudo mysql
```

```sql
CREATE DATABASE remory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'remory'@'localhost' IDENTIFIED BY 'strong-password';
GRANT ALL PRIVILEGES ON remory_db.* TO 'remory'@'localhost';
FLUSH PRIVILEGES;
```

## 프로젝트 배포

```bash
cd /srv
sudo git clone <repo-url> remory
sudo chown -R remory:remory /srv/remory
cd /srv/remory/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

운영 `.env` 예시:

```env
APP_NAME=Remory API
DEBUG=False
ENVIRONMENT=production

MYSQL_USER=remory
MYSQL_PASSWORD=strong-password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=remory_db

SECRET_KEY=replace-with-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14

CORS_ORIGINS=["https://your-frontend-domain.com"]

UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=52428800

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
STT_PROVIDER=mock
TTS_PROVIDER=mock
VOICE_CLONE_PROVIDER=mock
```

## Alembic

```bash
cd /srv/remory/backend
source .venv/bin/activate
alembic upgrade head
```

배포 전후 확인:

```bash
alembic current
alembic heads
```

## systemd

`/etc/systemd/system/remory-backend.service`:

```ini
[Unit]
Description=Remory Backend API
After=network.target mysql.service

[Service]
User=remory
Group=remory
WorkingDirectory=/srv/remory/backend
Environment="PATH=/srv/remory/backend/.venv/bin"
ExecStart=/srv/remory/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

적용:

```bash
sudo systemctl daemon-reload
sudo systemctl enable remory-backend
sudo systemctl start remory-backend
sudo systemctl status remory-backend
journalctl -u remory-backend -f
```

## Nginx

`/etc/nginx/sites-available/remory`:

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
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600;
    }
}
```

활성화:

```bash
sudo ln -s /etc/nginx/sites-available/remory /etc/nginx/sites-enabled/remory
sudo nginx -t
sudo systemctl reload nginx
```

HTTPS는 Certbot 또는 사용 중인 load balancer 정책에 맞춰 추가한다.

## CORS

프론트 도메인을 `.env`의 `CORS_ORIGINS`에 포함한다.

```env
CORS_ORIGINS=["https://app.example.com","http://localhost:5173"]
```

WebSocket은 브라우저에서 `wss://api.example.com/api/v1/ws/personas/{persona_id}/voice?token=...` 형태로 연결한다.

## GitHub Actions

현재 backend test workflow는 다음을 확인한다.

- Python 3.12 dependency 설치
- MySQL service container
- `.env` 생성
- `alembic upgrade head`
- `pytest -v`

배포 자동화까지 연결하려면 별도 job에서 SSH 또는 registry 기반 배포를 구성한다. 운영 서버에서 pull 후 다음 순서를 지킨다.

```bash
git pull
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart remory-backend
```

## 배포 체크리스트

- [ ] `.env` 운영 값 설정
- [ ] `DEBUG=False`
- [ ] 강한 `SECRET_KEY`
- [ ] MySQL DB/user/권한 생성
- [ ] `alembic upgrade head` 성공
- [ ] `uploads/` 쓰기 권한 확인
- [ ] systemd service active
- [ ] Nginx `nginx -t` 성공
- [ ] CORS에 프론트 도메인 등록
- [ ] `/health` 응답 확인
- [ ] `/docs` 접근 정책 확인
- [ ] WebSocket upgrade 확인
- [ ] 로그 확인: `journalctl -u remory-backend -f`

## 자주 발생한 오류

### alembic access denied

증상:

```text
Access denied for user 'remory'@'localhost'
```

해결:

```sql
GRANT ALL PRIVILEGES ON remory_db.* TO 'remory'@'localhost';
FLUSH PRIVILEGES;
```

`.env`의 DB 사용자/비밀번호/DB 이름과 실제 MySQL 계정을 맞춘다.

### systemd bad message

원인:

- service 파일에 잘못된 따옴표 또는 Windows CRLF가 들어감
- `ExecStart` 경로가 잘못됨
- `WorkingDirectory`가 없음

해결:

```bash
sudo systemctl daemon-reload
sudo systemctl status remory-backend
journalctl -u remory-backend -n 100
```

service 파일은 Linux 경로와 LF line ending으로 저장한다.

### ERR_CONNECTION_REFUSED

확인 순서:

1. Uvicorn/systemd가 실행 중인지 확인
2. `curl http://127.0.0.1:8000/health`
3. Nginx가 실행 중인지 확인
4. `sudo nginx -t`
5. 방화벽/security group에서 80/443이 열려 있는지 확인
6. 프론트 API base URL이 올바른지 확인

```bash
sudo systemctl status remory-backend
sudo systemctl status nginx
sudo ufw status
```
