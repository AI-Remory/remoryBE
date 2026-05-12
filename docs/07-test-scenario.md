# 07. Test Scenario

## 목차

- [Pytest 실행](#pytest-실행)
- [테스트 환경](#테스트-환경)
- [테스트 파일](#테스트-파일)
- [대표 API 시나리오](#대표-api-시나리오)
- [수동 점검](#수동-점검)

## Pytest 실행

```bash
pytest
```

특정 파일:

```bash
pytest tests/test_01_auth.py
pytest tests/test_19_realtime_voice.py
```

## 테스트 환경

`tests/conftest.py`는 `app.core.database.get_db`를 SQLite in-memory DB로 override한다. 테스트마다 `Base.metadata.create_all`/`drop_all`을 수행하므로 MySQL 없이 실행된다.

업로드 테스트는 다음 디렉터리를 정리한다.

```text
uploads/images
uploads/voices
uploads/photo_memories
uploads/verifications
uploads/chat_audio
uploads/chat_tts
```

## 테스트 파일

| 파일 | 범위 |
| --- | --- |
| `test_00_health.py` | `/health` |
| `test_01_auth.py` | register/login/me/refresh/logout |
| `test_02_target.py` | target CRUD |
| `test_03_consent.py`, `test_03_media.py` | consent, target media |
| `test_04_persona.py` | persona, voice profile |
| `test_05_chat.py` | chat/message/audio |
| `test_06_interview.py` | interview session/question/answer |
| `test_07_photo_memory.py` | photo memory |
| `test_08_storybook.py` | storybook/chapter |
| `test_09_share_group.py` | share link, group |
| `test_10_deletion.py` | deletion request |
| `test_11_consent_log.py`, `test_11_verification.py` | consent log, verification |
| `test_12_stt_service.py` - `test_14_voice_clone_service.py` | speech services |
| `test_15_audit_log.py` | audit log |
| `test_16_rate_limit.py` | usage/rate limit |
| `test_17_report.py` | report |
| `test_18_voice_profile_quality.py` | voice profile quality |
| `test_19_realtime_voice.py` | realtime voice WebSocket |

## 대표 API 시나리오

1. `POST /api/v1/auth/register`로 사용자와 token 생성.
2. `POST /api/v1/targets`로 target 생성.
3. `POST /api/v1/consents`로 photo/voice/persona 관련 consent 생성.
4. `POST /api/v1/targets/{target_id}/media`로 image/voice 업로드.
5. 테스트 fixture 또는 admin API로 verification 승인 상태 준비.
6. `POST /api/v1/targets/{target_id}/persona`로 persona 생성.
7. `POST /api/v1/personas/{persona_id}/chats`와 `POST /api/v1/chats/{chat_id}/messages`로 대화 검증.
8. `POST /api/v1/interviews`, question/answer 생성 후 `POST /api/v1/storybooks`.
9. `POST /api/v1/storybooks/{storybook_id}/share-links` 후 `GET /api/v1/share/{token}` 확인.
10. admin token으로 `/api/v1/admin/*` 권한 API 확인.

## 수동 점검

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

환경 변수 문제를 배포 전에 확인한다.

```bash
grep -E "^[A-Z_]+=" .env.example | cut -d= -f1 | sort > /tmp/env_example_keys.txt
grep -E "^[A-Z_]+=" .env | cut -d= -f1 | sort > /tmp/env_keys.txt
comm -13 /tmp/env_example_keys.txt /tmp/env_keys.txt
```

출력된 키는 현재 `Settings`에 없는 값이므로 제거한다.
