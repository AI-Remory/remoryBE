# Remory Backend TODO

## 0. 현재 코드 검증

먼저 기능 추가 전에 현재 백엔드 뼈대가 실제로 동작하는지 확인한다.

- [ ] `uvicorn app.main:app --reload` 실행 확인
- [ ] `http://localhost:8000/docs` Swagger 접속 확인
- [ ] MySQL 실행 확인
- [ ] `.env`의 `DATABASE_URL` 확인
- [ ] Alembic 마이그레이션 생성 성공
- [ ] `alembic upgrade head` 성공
- [ ] `POST /api/v1/targets` 테스트
- [ ] `GET /api/v1/targets` 테스트
- [ ] IntelliJ import 오류 해결
- [ ] `.env`, `.env.example`, `.gitignore` 정리

---

## 1. User/Auth 구현

모든 데이터는 사용자 소유권이 필요하므로, 다음 단계는 인증 기능이다.

### User/Auth

- [ ] `User` 모델 완성
- [ ] `UserCreate`, `UserLogin`, `UserResponse` schema 작성
- [ ] 비밀번호 해시 처리
- [ ] JWT Access Token 발급 기능 구현
- [ ] `get_current_user` dependency 구현
- [ ] 회원가입 API 구현: `POST /api/v1/auth/register`
- [ ] 로그인 API 구현: `POST /api/v1/auth/login`
- [ ] 내 정보 조회 API 구현: `GET /api/v1/auth/me`
- [ ] 이메일 중복 검사
- [ ] 로그인 실패 처리
- [ ] Auth 관련 Swagger 테스트

### Target과 User 연결

- [ ] `Target` 모델에 `user_id` 외래키 추가
- [ ] `User` ↔ `Target` 관계 설정
- [ ] 로그인한 사용자만 target 생성 가능하게 수정
- [ ] 로그인한 사용자의 target만 조회되게 수정
- [ ] 다른 사용자의 target 접근 차단
- [ ] Alembic migration 생성
- [ ] DB 반영 후 테스트

---

## 2. TargetMedia 업로드 구현

페르소나 생성 전에 target의 사진과 음성 파일 업로드 기능이 필요하다.

### 파일 저장 구조

- [ ] `uploads/` 폴더 생성
- [ ] `uploads/images/` 폴더 생성
- [ ] `uploads/voices/` 폴더 생성
- [ ] 파일 저장 service 작성
- [ ] 파일 삭제 service 작성
- [ ] 파일명 중복 방지 처리
- [ ] 파일 크기 저장
- [ ] MIME type 저장
- [ ] DB에는 파일 바이너리가 아니라 파일 경로와 메타데이터만 저장

### TargetMedia 모델/API

- [ ] `TargetMedia` 모델 완성
- [ ] target 파일 업로드 API 구현: `POST /api/v1/targets/{target_id}/media`
- [ ] target media 목록 조회 API 구현: `GET /api/v1/targets/{target_id}/media`
- [ ] media 단건 삭제 API 구현: `DELETE /api/v1/media/{media_id}`
- [ ] image/audio MIME type 검증
- [ ] 본인 target에만 업로드 가능하게 권한 검사
- [ ] 삭제 시 실제 파일도 삭제
- [ ] Swagger에서 이미지 업로드 테스트
- [ ] Swagger에서 음성 업로드 테스트

---

## 3. ConsentLog 구현

음성, 사진, 페르소나 생성은 민감 데이터이므로 동의 기록을 남겨야 한다.

- [ ] `ConsentLog` 모델 완성
- [ ] 동의 타입 enum 설계
  - [ ] `PHOTO_UPLOAD`
  - [ ] `VOICE_UPLOAD`
  - [ ] `PERSONA_CREATE`
  - [ ] `AI_RESPONSE_NOTICE`
  - [ ] `STORYBOOK_SHARE`
- [ ] 동의 저장 API 구현: `POST /api/v1/consents`
- [ ] 내 동의 내역 조회 API 구현: `GET /api/v1/consents`
- [ ] target별 동의 여부 확인 service 작성
- [ ] 페르소나 생성 전에 동의 여부 검사
- [ ] 음성 업로드 전에 동의 여부를 검사할지 정책 결정

---

## 4. Persona 생성 Mock 구현

MVP에서는 실제 AI 학습 대신 mock persona profile을 생성한다.

### Persona 모델/서비스

- [ ] `Persona` 모델 완성
- [ ] `PersonaVoiceProfile` 모델 완성
- [ ] `PersonaCreateRequest` schema 작성
- [ ] `PersonaResponse` schema 작성
- [ ] `persona_service.py` 작성
- [ ] `ai_service.py`에 mock persona 생성 함수 작성
- [ ] target 설명 데이터 기반으로 persona profile 생성
- [ ] persona 상태값 추가
  - [ ] `PENDING`
  - [ ] `READY`
  - [ ] `FAILED`

### Persona API

- [ ] 페르소나 생성 요청 API 구현: `POST /api/v1/targets/{target_id}/persona`
- [ ] 페르소나 상태 조회 API 구현: `GET /api/v1/personas/{persona_id}/status`
- [ ] 페르소나 상세 조회 API 구현: `GET /api/v1/personas/{persona_id}`
- [ ] 본인 target 기반 persona만 접근 가능하게 권한 검사
- [ ] 동의 없는 경우 생성 차단
- [ ] target media가 부족한 경우 경고 응답 처리

---

## 5. Persona Chat 구현

서비스 핵심 기능인 페르소나와의 텍스트/음성 대화를 구현한다.

### Chat 모델/서비스

- [ ] `PersonaChat` 모델 완성
- [ ] `PersonaMessage` 모델 완성
- [ ] sender type 설계
  - [ ] `USER`
  - [ ] `PERSONA`
  - [ ] `SYSTEM`
- [ ] message type 설계
  - [ ] `TEXT`
  - [ ] `AUDIO`
- [ ] 대화방 생성 service 작성
- [ ] 메시지 저장 service 작성
- [ ] mock persona 응답 생성 service 작성

### Chat API

- [ ] 페르소나 대화방 시작 API 구현: `POST /api/v1/personas/{persona_id}/chats`
- [ ] 텍스트 메시지 전송 API 구현: `POST /api/v1/chats/{chat_id}/messages`
- [ ] 메시지 목록 조회 API 구현: `GET /api/v1/chats/{chat_id}/messages`
- [ ] 음성 입력 업로드 API 구현: `POST /api/v1/chats/{chat_id}/audio`
- [ ] 음성 입력은 MVP에서 파일 업로드만 받고 STT는 mock 처리
- [ ] persona 응답은 mock 텍스트로 반환
- [ ] TTS 음성 응답은 MVP에서 placeholder URL 또는 기본 TTS 예정값만 반환

---

## 6. AIInterviewSession 구현

target 보완 질문, 사진 기반 질문, AI 선제 질문을 하나의 session 구조로 관리한다.

- [ ] `AIInterviewSession` 모델 작성
- [ ] `AIInterviewMessage` 또는 `AIInterviewAnswer` 모델 작성 여부 결정
- [ ] session type 설계
  - [ ] `TARGET_PROFILE`
  - [ ] `PHOTO_MEMORY`
  - [ ] `SELF_STORY`
- [ ] mock 질문 생성 함수 작성
- [ ] 사용자 답변 저장
- [ ] 꼬리 질문 mock 생성
- [ ] 인터뷰 세션 생성 API 구현: `POST /api/v1/interviews`
- [ ] AI 질문 생성 API 구현: `POST /api/v1/interviews/{session_id}/questions`
- [ ] 사용자 답변 저장 API 구현: `POST /api/v1/interviews/{session_id}/answers`
- [ ] 인터뷰 세션 조회 API 구현: `GET /api/v1/interviews/{session_id}`
- [ ] target 보완 질문 10~15개 기본 세트 작성
- [ ] 사진 기반 질문 기본 세트 작성
- [ ] AI 선제 질문 기본 세트 작성

---

## 7. PhotoMemory 구현

사진 기반 스토리북 생성을 위한 사진 기억 객체를 구현한다.

- [ ] `PhotoMemory` 모델 작성
- [ ] 사진 업로드와 PhotoMemory 연결
- [ ] 사진 설명/날짜/장소/감정 키워드 저장
- [ ] 사진 기반 인터뷰 세션 연결
- [ ] PhotoMemory 생성 API 구현: `POST /api/v1/photo-memories`
- [ ] PhotoMemory 조회 API 구현: `GET /api/v1/photo-memories/{photo_memory_id}`
- [ ] 사진 기반 질문 생성 mock 연결

---

## 8. StoryBook 구현

사진/대화/인터뷰 결과를 스토리북으로 생성한다.

### StoryBook 모델

- [ ] `StoryBook` 모델 완성
- [ ] `StoryChapter` 모델 완성
- [ ] `StoryVoiceNarration` 모델 작성
- [ ] StoryBook status 설계
  - [ ] `DRAFT`
  - [ ] `GENERATED`
  - [ ] `SHARED`
- [ ] 공개 범위 설계
  - [ ] `PRIVATE`
  - [ ] `LINK`
  - [ ] `GROUP`
  - [ ] `PUBLIC`

### StoryBook API

- [ ] 스토리북 생성 API 구현: `POST /api/v1/storybooks`
- [ ] 내 스토리북 목록 조회 API 구현: `GET /api/v1/storybooks`
- [ ] 스토리북 상세 조회 API 구현: `GET /api/v1/storybooks/{storybook_id}`
- [ ] 챕터 목록 조회 API 구현: `GET /api/v1/storybooks/{storybook_id}/chapters`
- [ ] 스토리북 재생성 API 구현: `POST /api/v1/storybooks/{storybook_id}/regenerate`
- [ ] mock storybook 생성 service 작성
- [ ] 인터뷰 답변 기반 챕터 자동 생성 mock 구현
- [ ] 원본 음성 또는 내레이션 파일 연결 구조 작성

---

## 9. ShareLink 구현

A 사용자가 만든 스토리북을 B 사용자에게 전달하는 기능이다.

- [ ] `ShareLink` 모델 작성
- [ ] 공유 token 생성
- [ ] 만료일 설정
- [ ] 조회 권한 설정
- [ ] 공유 링크 생성 API 구현: `POST /api/v1/storybooks/{storybook_id}/share-links`
- [ ] 공유 링크 조회 API 구현: `GET /api/v1/share/{token}`
- [ ] 공유 링크 비활성화 API 구현: `DELETE /api/v1/share-links/{share_link_id}`
- [ ] 본인 스토리북만 공유 가능하게 검사
- [ ] 공유받은 사용자가 볼 수 있는 응답 DTO 분리

---

## 10. MemoryGroup 구현

그룹 내에서 스토리북을 공유하고 열람할 수 있게 한다.

- [ ] `MemoryGroup` 모델 완성
- [ ] `GroupMember` 모델 완성
- [ ] group role 설계
  - [ ] `OWNER`
  - [ ] `MEMBER`
  - [ ] `VIEWER`
- [ ] 그룹 생성 API 구현: `POST /api/v1/groups`
- [ ] 그룹 목록 조회 API 구현: `GET /api/v1/groups`
- [ ] 그룹 멤버 초대 API 구현: `POST /api/v1/groups/{group_id}/members`
- [ ] 그룹에 스토리북 공유 API 구현: `POST /api/v1/groups/{group_id}/storybooks/{storybook_id}`
- [ ] 그룹 내 스토리북 목록 조회 API 구현: `GET /api/v1/groups/{group_id}/storybooks`
- [ ] MVP에서는 보기 권한만 우선 구현
- [ ] 댓글/좋아요/재공유는 후순위 처리

---

## 11. DeletionRequest 구현

민감 데이터 삭제 요청과 실제 삭제 처리 이력을 관리한다.

- [ ] `DeletionRequest` 모델 작성
- [ ] 삭제 대상 타입 설계
  - [ ] `TARGET`
  - [ ] `MEDIA`
  - [ ] `PERSONA`
  - [ ] `CHAT`
  - [ ] `STORYBOOK`
  - [ ] `ACCOUNT`
- [ ] 삭제 요청 생성 API 구현: `POST /api/v1/deletion-requests`
- [ ] 삭제 요청 내역 조회 API 구현: `GET /api/v1/deletion-requests`
- [ ] 실제 삭제 처리 service 작성
- [ ] 파일 삭제 포함 처리
- [ ] 삭제 실패 시 로그 저장
- [ ] 논리 삭제/물리 삭제 정책 결정

---

## 12. Frontend 연동 TODO

백엔드 API가 어느 정도 완성되면 프론트엔드와 연결한다.

### 초기 세팅

- [ ] React + Vite + TypeScript 생성
- [ ] Tailwind 또는 CSS 프레임워크 결정
- [ ] API client 설정
- [ ] 라우터 설정
- [ ] `.env`에 `VITE_API_BASE_URL=http://localhost:8000` 설정

### 주요 화면

- [ ] 로그인 화면
- [ ] 회원가입 화면
- [ ] 홈 화면
- [ ] Target 생성 화면
- [ ] Target 목록 화면
- [ ] Target 상세 화면
- [ ] 사진/음성 업로드 화면
- [ ] 동의 체크 화면
- [ ] 페르소나 생성 화면
- [ ] 페르소나 채팅 화면
- [ ] 사진 기반 스토리북 생성 화면
- [ ] AI 질문 기반 스토리북 생성 화면
- [ ] 스토리북 상세 화면
- [ ] 공유 링크 화면
- [ ] 그룹 화면

---

## 13. 발표/데모 TODO

아이디어톤에서는 실제 구현 범위와 데모 흐름이 중요하다.

- [ ] 사용자 회원가입
- [ ] target “엄마” 생성
- [ ] 엄마 사진 업로드
- [ ] 엄마 음성 업로드
- [ ] AI가 target 관련 질문
- [ ] 사용자가 말투/성격/에피소드 입력
- [ ] 페르소나 생성
- [ ] “나 오늘 너무 힘들었어” 입력
- [ ] 엄마 페르소나가 응답
- [ ] 개인 사진 업로드
- [ ] AI가 사진에 대해 질문
- [ ] 답변 기반 스토리북 생성
- [ ] 스토리북 공유 링크 생성
- [ ] B 사용자가 링크로 열람

---

## 14. GitHub / Alembic 공유 규칙

### GitHub에 올려야 하는 것

- [ ] `backend/app/`
- [ ] `backend/alembic/`
- [ ] `backend/alembic/versions/*.py`
- [ ] `backend/alembic.ini`
- [ ] `backend/requirements.txt`
- [ ] `backend/.env.example`
- [ ] `frontend/src/`
- [ ] `frontend/package.json`
- [ ] 루트 `README.md`
- [ ] 루트 `.gitignore`

### GitHub에 올리면 안 되는 것

- [ ] `backend/.env`
- [ ] `frontend/.env`
- [ ] `backend/.venv/`
- [ ] `frontend/node_modules/`
- [ ] `backend/uploads/`
- [ ] `__pycache__/`
- [ ] `*.pyc`
- [ ] 로컬 DB 파일

### Alembic 규칙

- [ ] DB 모델을 수정한 사람은 migration 파일도 같이 생성한다.
- [ ] `backend/alembic/versions/*.py`는 반드시 커밋한다.
- [ ] 팀원은 pull 받은 뒤 `alembic upgrade head`를 실행한다.
- [ ] 모델만 수정하고 migration을 누락하지 않는다.

```bash
# 모델 변경 후
cd backend
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head

# 커밋 예시
git add backend/app backend/alembic/versions
git commit -m "feat: add user and target schema"
```

---

## 15. 최종 우선순위

### 지금 당장 할 것

1. 현재 코드 실행 검증
2. Alembic migration 성공 확인
3. Target API 테스트
4. Auth/User 구현
5. Target에 `user_id` 연결
6. TargetMedia 업로드 구현

### 그다음 할 것

7. ConsentLog 구현
8. Persona mock 생성 구현
9. PersonaChat/Message 구현
10. AIInterviewSession 구현
11. StoryBook/Chapter 구현

### 마지막에 할 것

12. ShareLink 구현
13. MemoryGroup 구현
14. DeletionRequest 구현
15. 프론트 연결
16. 데모 시나리오 정리

---

## 한 줄 정리

현재 개발 순서는 다음이 가장 안전하다.

```text
User → Target → Media → Consent → Persona → Chat → Interview → StoryBook → Share/Group → Delete
```

AI 기능부터 바로 만들지 말고, 먼저 사용자 소유권, 파일 업로드, 동의, 삭제 가능성을 안정적으로 잡아야 한다.
