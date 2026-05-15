# 02. Backend API (Code-Based)

## OpenVoice Voice Profile/Evaluate Flow (2026-05-15)
- Endpoints are unchanged:
  - `POST /api/v1/personas/{persona_id}/voice-profile`
  - `POST /api/v1/personas/{persona_id}/voice-profile/evaluate`
  - `PATCH /api/v1/personas/{persona_id}/voice-profile/user-confirm`
- Security gates are unchanged and still required:
  - approved target verification
  - `voice_upload_consent`
  - `voice_cloning_consent`
- Evaluate behavior:
  - OpenVoice provider now creates target speaker embedding at:
    - `OPENVOICE_OUTPUT_DIR/profiles/persona_{persona_id}/target_se.pth`
  - profile metadata json is saved in the same profile directory
  - success => `status=READY`, `provider=openvoice`, `model_name=openvoice-v2`, `voice_profile_path` populated
  - failure => `status=FAILED` or `NEEDS_MORE_SAMPLES` with `error_message` (max 500 chars)
- Sample audio:
  - evaluate generates real sample wav via OpenVoice and stores `sample_audio_path`
  - `user-confirm` remains allowed only when `status=READY`

## 기준
- 코드 기준: `app/api/v1/endpoints/*`, `app/schemas/*`, `app/services/*`, `app/deps.py`
- OpenAPI와 코드가 다르면 코드 기준으로 작성
- WebSocket은 OpenAPI 자동 문서 대상이 아니므로 별도 섹션 제공

## 공통 규칙
- Base URL: `/api/v1`
- Health: `GET /health`
- 인증: `Authorization: Bearer <access_token>`
- 기본 에러 처리
  - `400`: 잘못된 입력/상태. 프론트 안내: 입력값 또는 선행 조건 확인
  - `401`: 로그인 필요/토큰 무효. 프론트 안내: 재로그인 또는 토큰 갱신
  - `403`: 권한 없음/정책 미충족. 프론트 안내: 권한 또는 동의/승인 상태 확인
  - `404`: 리소스 없음. 프론트 안내: 삭제/만료 여부 확인
  - `409`: 상태 충돌(해당 API에서 명시적 사용은 적음)
  - `422`: FastAPI validation 에러
  - `500`: 서버 오류
- 파일 응답 API는 모두 권한 검사 후 `FileResponse` 반환
- 운영 환경에서 `/uploads` public static 사용 금지

## 인증/권한 의존성
- `get_current_user`: 로그인 사용자
- `get_admin_user`: `user.role == ADMIN`만 허용
- Owner-only 여부는 서비스 레이어에서 리소스 소유자 검사로 강제

## 응답 스키마 핵심 필드
- `UserResponse`: `id`, `email`, `nickname`, `role(USER|ADMIN)`, `created_at`, `updated_at`
- `TargetResponse`: `id`, `user_id`, `name`, `description`, `target_type`, `is_deleted`, timestamps
- `TargetDetailResponse`: `TargetResponse` + `media_count`, `has_persona`
- `TargetMediaResponse`: `id`, `target_id`, `media_type`, `mime_type`, `file_size`, `file_api_url`, `file_path(deprecated)`
- `ConsentResponse`: `id`, `user_id`, `target_id`, `consent_type`, `is_agreed`, `is_consented`, `agreed_at`, `revoked_at`
- `VerificationRequestResponse`: `status`, `verification_type`, `original_filename`, `mime_type`, `file_size`, `reviewed_*`
- `PersonaDetailResponse`: 페르소나 요약 + `voice_profile`
- `PersonaVoiceProfileResponse`: `status`, `review_status`, 품질 점수, 참조 음성 메타
- `PersonaMessageResponse`: `message_type`, `content`, `audio_api_url`, `audio_file_path(deprecated)`
- `AIInterviewSessionDetailResponse`: 세션 + `questions[]` + `answers[]`
- `PhotoMemoryResponse`: 메타 + `image_api_url`, `file_path(deprecated)`
- `StoryBookDetailResponse`: 스토리북 + `chapters[]`
- `ShareLinkResponse`: `token`, `share_url`, `is_active`, `expires_at`
- `DeletionRequestResponse`: `target_type`, `target_id`, `status`, `processed_at`, `error_message`
- `ReportResponse`: 신고 정보 + 처리 상태
- `AuditLogResponse`: `action`, `target_type`, `target_id`, `description`, `created_at`
- `UsageLimitResponse` / `PersonaUsageLimitResponse` / `RateLimitEventResponse`: 사용량/제한/이벤트

---

## Auth / User
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 회원가입 | POST | `/auth/register` | 사용자 생성 + 토큰 발급 | N | Public | N | - | - | `application/json` | `RegisterRequest(email,nickname,password)` | `201 AuthResponse` | `access_token`, `refresh_token`, `user(role 포함)` | `400 이메일/닉네임 중복`, `422 validation` | 회원가입 완료 후 로그인 상태 전환 | `/auth/me` | - |
| 회원가입 별칭 | POST | `/auth/sign-up` | register와 동일 | N | Public | N | - | - | `application/json` | `RegisterRequest` | `201 AuthResponse` | 동일 | 동일 | 구버전 클라이언트 호환 | `/auth/register` | - |
| 로그인 | POST | `/auth/login` | 인증 후 토큰 발급 | N | Public | N | - | - | `application/json` | `LoginRequest(email,password)` | `200 AuthResponse` | 동일 | `401 인증 실패` | 로그인 화면 | `/auth/refresh-token` | - |
| 내 정보 조회 | GET | `/auth/me` | 현재 사용자 정보 | Y | USER/ADMIN | Y(자기자신) | - | - | - | - | `200 UserResponse` | `id,email,nickname,role` | `401` | 앱 초기 사용자 상태 | Admin 메뉴 노출 판단 | - |
| 토큰 재발급 | POST | `/auth/refresh-token` | refresh token rotation | N | Public | N | - | - | `application/json` | `RefreshTokenRequest` | `200 TokenResponse` | `access_token,refresh_token` | `401 refresh token 무효/만료` | API 에러 인터셉터 | `/auth/login` | - |
| 로그아웃 | POST | `/auth/logout` | refresh token revoke | N | Public | N | - | - | `application/json` | `LogoutRequest` | `200 MessageResponse` | `message` | `401` | 로그아웃 액션 | `/auth/refresh-token` | - |

## Target
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 타겟 생성 | POST | `/targets` | 관계 대상 생성 | Y | USER/ADMIN | Y | - | - | `application/json` | `TargetCreateRequest` | `201 TargetResponse` | 타겟 기본 필드 | `422 validation` | Target 생성 화면 | `/targets/{id}` | - |
| 타겟 목록 | GET | `/targets` | 내 타겟 목록(페이지) | Y | USER/ADMIN | Y | - | `skip,limit` | - | - | `200 PaginatedResponse[TargetResponse]` | `total,skip,limit,items[]` | `422` | 목록 렌더링 | `/targets/{id}` | - |
| 타겟 상세 | GET | `/targets/{target_id}` | 타겟 + media/persona 여부 | Y | USER/ADMIN | Y | `target_id` | - | - | - | `200 TargetDetailResponse` | `media_count,has_persona` 포함 | `403/404` | 상세 화면 | media/persona API | - |
| 타겟 수정 | PUT | `/targets/{target_id}` | 타겟 정보 수정 | Y | USER/ADMIN | Y | `target_id` | - | `application/json` | `TargetUpdateRequest` | `200 TargetResponse` | 수정 반영 필드 | `403/404` | 편집 화면 | 상세 API | - |
| 타겟 삭제 | DELETE | `/targets/{target_id}` | 소프트 삭제 | Y | USER/ADMIN | Y | `target_id` | - | - | - | `204` | body 없음 | `403/404` | 목록에서 제외 처리 | 상세/목록 API | - |

## TargetMedia
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 미디어 업로드 | POST | `/targets/{target_id}/media` | 이미지/음성 업로드 | Y | USER/ADMIN | Y | `target_id` | - | `multipart/form-data` | `media_type`, `file` | `201 MediaUploadResponse` | `file_api_url` 사용, `file_path` deprecated | `403 동의/소유권`, `400 MIME/용량` | 업로드 후 목록 갱신 | Consent, Target | - |
| 미디어 목록 | GET | `/targets/{target_id}/media` | 타겟 미디어 목록 | Y | USER/ADMIN | Y | `target_id` | - | - | - | `200 TargetMediaResponse[]` | `file_api_url` 포함 | `403/404` | 썸네일/오디오 목록 | 파일 조회 API | - |
| 미디어 파일 조회 | GET | `/targets/{target_id}/media/{media_id}/file` | 보호된 파일 조회 | Y | USER/ADMIN | Y | `target_id`,`media_id` | - | - | - | `200 file` | MIME은 저장값 우선 | `403 경로/권한`, `404 파일없음` | `fetch + blob + objectURL` | 목록 API | - |
| 미디어 삭제 | DELETE | `/media/{media_id}` | 미디어 및 파일 삭제 | Y | USER/ADMIN | Y | `media_id` | - | - | - | `200 MediaDeleteResponse` | `message` | `403/404` | UI에서 즉시 제거 | 목록 API | - |

## ConsentLog
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 동의 생성 | POST | `/consents` | 동의 이력 생성 | Y | USER/ADMIN | Y | - | - | `application/json` | `ConsentCreate` | `201 ConsentResponse` | 동의 상태/버전/시각 | `422`, `403 target 권한`, `500 DB` | 체크박스 제출 | Persona, Share, Group | - |
| 내 동의 목록 | GET | `/consents` | 내 동의 전체 조회 | Y | USER/ADMIN | Y | - | - | - | - | `200 ConsentResponse[]` | 최신순 | `401` | 내 설정 화면 | create/revoke | - |
| 타겟별 동의 목록 | GET | `/targets/{target_id}/consents` | 타겟 단위 조회 | Y | USER/ADMIN | Y | `target_id` | - | - | - | `200 ConsentResponse[]` | 타겟 필터 | `403/404` | 타겟 상세 동의 섹션 | create/revoke | - |
| 동의 철회 | PATCH | `/consents/{consent_id}/revoke` | 동의 철회 | Y | USER/ADMIN | Y | `consent_id` | - | - | - | `200 ConsentRevokeResponse` | `is_agreed=false` | `403/404` | 토글 비활성화 | create/list | - |

## TargetVerificationRequest
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 관계 입증 제출 | POST | `/targets/{target_id}/verification-requests` | 파일 업로드 + 요청 생성 | Y | USER/ADMIN | Y | `target_id` | - | `multipart/form-data` | `verification_type_param`, `applicant_note`, `file` | `201 VerificationRequestResponse` | 상태 `PENDING` 시작 | `400 파일 타입/크기`, `422 type` | 제출 화면 | Admin 검수 API | - |
| 타겟 요청 목록 | GET | `/targets/{target_id}/verification-requests` | 타겟별 요청 조회 | Y | USER/ADMIN | Y | `target_id` | `skip,limit` | - | - | `200 PaginatedResponse[...]` | `items[]` | `403/404` | 히스토리 목록 | detail API | - |
| 요청 상세 | GET | `/verification-requests/{request_id}` | 본인 또는 타겟 소유자 조회 | Y | USER/ADMIN | 조건부 | `request_id` | - | - | - | `200 VerificationRequestDetailResponse` | 파일 메타/심사 결과 | `403/404` | 상태 배지 | Admin 검수 API | - |

## Persona / PersonaVoiceProfile
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 페르소나 생성 | POST | `/targets/{target_id}/persona` | 타겟 기반 생성 | Y | USER/ADMIN | Y | `target_id` | - | - | - | `201 PersonaDetailResponse` | status, prompt, voice_profile | `403 verification/consent 조건`, `404` | 생성 CTA | Verification, Consent, Media | - |
| 페르소나 조회 | GET | `/personas/{persona_id}` | 내 페르소나 조회 | Y | USER/ADMIN | Y | `persona_id` | - | - | - | `200 PersonaDetailResponse` | 동일 | `403/404` | 상세 페이지 | status/profile/chat | - |
| 페르소나 상태 | GET | `/personas/{persona_id}/status` | 상태만 조회 | Y | USER/ADMIN | Y | `persona_id` | - | - | - | `200 PersonaStatusResponse` | `status` | `403/404` | 폴링 | persona GET | - |
| 보이스 프로필 생성 | POST | `/personas/{persona_id}/voice-profile` | clone 준비 상태 생성 | Y | USER/ADMIN | Y | `persona_id` | - | - | - | `201 PersonaVoiceProfileResponse` | `status(PENDING/NEEDS_MORE_SAMPLES)` | `403 consent/verification`, `404` | 음성 준비 단계 | evaluate/profile | - |
| 보이스 프로필 조회 | GET | `/personas/{persona_id}/voice-profile` | 프로필 상세 | Y | USER/ADMIN | Y | `persona_id` | - | - | - | `200 PersonaVoiceProfileResponse` | 품질 점수/샘플 경로 | `403/404` | 상태 카드 | create/evaluate | - |
| 보이스 프로필 평가 | POST | `/personas/{persona_id}/voice-profile/evaluate` | 품질평가 + 샘플 생성 | Y | USER/ADMIN | Y | `persona_id` | - | - | - | `200 PersonaVoiceProfileResponse` | READY 여부 | `403`, `404` | 평가 버튼 | user-confirm | - |
| 보이스 프로필 사용자 확정 | PATCH | `/personas/{persona_id}/voice-profile/user-confirm` | 사용자 승인 | Y | USER/ADMIN | Y | `persona_id` | - | `application/json` | `VoiceProfileReviewRequest` | `200 PersonaVoiceProfileResponse` | `review_status=USER_CONFIRMED` | `400 READY 아님` | 확인 버튼 | Admin voice-profile | - |

## PersonaChat / PersonaMessage
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 채팅 생성 | POST | `/personas/{persona_id}/chats` | 페르소나 채팅방 생성 | Y | USER/ADMIN | Y | `persona_id` | - | `application/json` | `PersonaChatCreateRequest` | `201 PersonaChatResponse` | chat id/title | `403/404` | 채팅 시작 | 메시지 API | - |
| 채팅 목록 | GET | `/personas/{persona_id}/chats` | 채팅 목록 | Y | USER/ADMIN | Y | `persona_id` | - | - | - | `200 PersonaChatResponse[]` | created desc | `403/404` | 채팅 리스트 | create/message list | - |
| 텍스트 메시지 | POST | `/chats/{chat_id}/messages` | 사용자 텍스트 + 페르소나 응답 | Y | USER/ADMIN | Y | `chat_id` | - | `application/json` | `PersonaMessageCreateRequest` | `201 PersonaMessagePairResponse` | `user_message`, `persona_message` | `403/404`, `422` | 대화 렌더링 | list/audio | - |
| 오디오 메시지 | POST | `/chats/{chat_id}/audio` | 업로드 음성 STT 후 응답 | Y | USER/ADMIN | Y | `chat_id` | - | `multipart/form-data` | `file`, `generate_audio` | `201 PersonaMessagePairResponse` | 사용자 AUDIO 메시지 포함 | `400 MIME/size`, `403` | 음성 전송 UI | audio file API | - |
| 메시지 목록 | GET | `/chats/{chat_id}/messages` | 채팅 메시지 오름차순 | Y | USER/ADMIN | Y | `chat_id` | - | - | - | `200 PersonaMessageResponse[]` | `audio_api_url` 사용 | `403/404` | 메시지 리스트 | file API | - |
| 메시지 오디오 조회 | GET | `/chats/{chat_id}/messages/{message_id}/audio` | 보호된 오디오 파일 반환 | Y | USER/ADMIN | Y | `chat_id`,`message_id` | - | - | - | `200 file` | MIME 추론(웹엠은 audio/webm 보정) | `403`, `404` | `fetch+blob+audio` | 메시지 목록 | - |

## AIInterviewSession / Question / Answer
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 인터뷰 세션 생성 | POST | `/interviews` | 인터뷰 세션 생성 | Y | USER/ADMIN | Y | - | - | `application/json` | `AIInterviewSessionCreateRequest` | `201 AIInterviewSessionResponse` | session_type/status | `403`, `422` | 인터뷰 시작 | question/answer | `PHOTO_MEMORY 타입에서 photo_memory_id 필수 여부 TODO` |
| 인터뷰 상세 | GET | `/interviews/{session_id}` | 질문/답변 포함 상세 | Y | USER/ADMIN | Y | `session_id` | - | - | - | `200 AIInterviewSessionDetailResponse` | `questions[].answers[]` | `403/404` | 상세 렌더링 | 질문/답변 생성 | - |
| 질문 생성 | POST | `/interviews/{session_id}/questions` | 다음 질문 생성 | Y | USER/ADMIN | Y | `session_id` | - | `application/json` | `AIInterviewQuestionCreateRequest?` | `201 AIInterviewQuestionResponse` | `question_text`, `order_index` | `403/404` | 다음 질문 버튼 | session detail | - |
| 답변 생성 | POST | `/interviews/{session_id}/answers` | 답변 저장 | Y | USER/ADMIN | Y | `session_id` | - | `application/json` | `AIInterviewAnswerCreateRequest` | `201 AIInterviewAnswerResponse` | text/audio path | `422 최소 one-of`, `403/404` | 답변 제출 | session detail | - |

## PhotoMemory
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 포토메모리 업로드 | POST | `/photo-memories` | 이미지 업로드 | Y | USER/ADMIN | Y | - | - | `multipart/form-data` | `title,description,taken_at,location,file` | `201 PhotoMemoryResponse` | `image_api_url` 사용 | `400 image MIME/size`, `422` | 업로드 폼 | image API | - |
| 목록 | GET | `/photo-memories` | 내 포토메모리 목록 | Y | USER/ADMIN | Y | - | - | - | - | `200 PhotoMemoryResponse[]` | 최신순 | `401` | 갤러리 | detail/delete | - |
| 상세 | GET | `/photo-memories/{photo_memory_id}` | 단건 조회 | Y | USER/ADMIN | Y | `photo_memory_id` | - | - | - | `200 PhotoMemoryResponse` | 메타 | `403/404` | 상세 패널 | image API | - |
| 이미지 파일 조회 | GET | `/photo-memories/{photo_memory_id}/image` | 보호된 이미지 조회 | Y | USER/ADMIN | Y | `photo_memory_id` | - | - | - | `200 file` | MIME은 저장값 우선 | `403 경로/권한`, `404` | `fetch+blob+img` | list/detail | - |
| 삭제 | DELETE | `/photo-memories/{photo_memory_id}` | 파일 삭제 + soft delete | Y | USER/ADMIN | Y | `photo_memory_id` | - | - | - | `200 PhotoMemoryDeleteResponse` | `message` | `403/404` | 삭제 반영 | list | - |

## StoryBook / StoryChapter / StoryVoiceNarration
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 스토리북 생성 | POST | `/storybooks` | 인터뷰/포토 기반 생성 | Y | USER/ADMIN | Y | - | - | `application/json` | `StoryBookCreateRequest` | `201 StoryBookDetailResponse` | `chapters[]` 포함 | `422 source 누락`, `403` | 생성 화면 | interview/photo | - |
| 스토리북 목록 | GET | `/storybooks` | 내 목록 | Y | USER/ADMIN | Y | - | - | - | - | `200 StoryBookResponse[]` | 메타만 | `401` | 목록 | detail | - |
| 스토리북 상세 | GET | `/storybooks/{storybook_id}` | 챕터 포함 상세 | Y | USER/ADMIN | Y | `storybook_id` | - | - | - | `200 StoryBookDetailResponse` | chapters | `403/404` | 상세 | chapters API | - |
| 챕터 목록 | GET | `/storybooks/{storybook_id}/chapters` | 챕터만 조회 | Y | USER/ADMIN | Y | `storybook_id` | - | - | - | `200 StoryChapterResponse[]` | order asc | `403/404` | 챕터 탭 | detail | - |
| 스토리북 재생성 | POST | `/storybooks/{storybook_id}/regenerate` | 기존 source로 재생성 | Y | USER/ADMIN | Y | `storybook_id` | - | - | - | `200 StoryBookDetailResponse` | summary/chapters 갱신 | `403/404` | regenerate 버튼 | detail | - |
| StoryVoiceNarration | - | - | 별도 HTTP API 없음 | - | - | - | - | - | - | - | - | 모델만 존재 | - | - | **확인 필요: 현재 라우터 없음** |

## ShareLink
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 공유 링크 생성 | POST | `/storybooks/{storybook_id}/share-links` | 토큰 링크 생성 | Y | USER/ADMIN | Y | `storybook_id` | - | `application/json` | `ShareLinkCreateRequest?` | `201 ShareLinkResponse` | `share_url`, `token` | `403 consent 필요`, `404` | 공유 버튼 | Consent, public share | - |
| 공유 링크 목록 | GET | `/storybooks/{storybook_id}/share-links` | 링크 조회 | Y | USER/ADMIN | Y | `storybook_id` | - | - | - | `200 ShareLinkResponse[]` | 활성/만료 상태 | `403/404` | 관리 리스트 | disable | - |
| 공개 링크 조회 | GET | `/share/{token}` | 공개 읽기 | N | Public | N | `token` | - | - | - | `200 PublicSharedStoryBookResponse` | title/summary/chapters | `403 비활성/만료`, `404` | 공개 페이지 | share-link 생성 | - |
| 공유 링크 비활성화 | PATCH | `/share-links/{share_link_id}/disable` | 링크 차단 | Y | USER/ADMIN | Y | `share_link_id` | - | - | - | `200 ShareLinkDisableResponse` | `is_active=false` | `403/404` | 관리 액션 | list/public read | - |

## MemoryGroup / GroupMember / GroupStoryBook
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 그룹 생성 | POST | `/groups` | 그룹 생성 + OWNER 가입 | Y | USER/ADMIN | Y | - | - | `application/json` | `MemoryGroupCreateRequest` | `201 MemoryGroupResponse` | group 기본 필드 | `422` | 그룹 생성 | 멤버/공유 API | - |
| 그룹 목록 | GET | `/groups` | 내가 속한 그룹 | Y | USER/ADMIN | Y | - | - | - | - | `200 MemoryGroupResponse[]` | 활성 멤버 기준 | `401` | 목록 | detail | - |
| 그룹 상세 | GET | `/groups/{group_id}` | 내 역할 포함 상세 | Y | USER/ADMIN | Y(멤버) | `group_id` | - | - | - | `200 MemoryGroupDetailResponse` | `my_role` 포함 | `403/404` | 상세 | members/storybooks | - |
| 멤버 추가 | POST | `/groups/{group_id}/members` | OWNER만 멤버 초대 | Y | USER/ADMIN | Y | `group_id` | - | `application/json` | `GroupMemberCreateRequest` | `201 GroupMemberResponse` | role 포함 | `403 owner만`, `404 user/group` | 초대 UI | member list | - |
| 멤버 목록 | GET | `/groups/{group_id}/members` | 활성 멤버 조회 | Y | USER/ADMIN | Y(멤버) | `group_id` | - | - | - | `200 GroupMemberResponse[]` | role 표시 | `403/404` | 멤버 리스트 | add member | - |
| 스토리북 그룹 공유 | POST | `/groups/{group_id}/storybooks/{storybook_id}` | 그룹에 공유 | Y | USER/ADMIN | Y(그룹 접근 + 책 소유) | `group_id`,`storybook_id` | - | - | - | `201 GroupStoryBookResponse` | 공유 식별자 | `403 consent/권한`, `404` | 공유 액션 | list group books | - |
| 그룹 스토리북 목록 | GET | `/groups/{group_id}/storybooks` | 그룹 공유 책 목록 | Y | USER/ADMIN | Y(멤버) | `group_id` | - | - | - | `200 GroupStoryBookListItemResponse[]` | title/summary/visibility | `403/404` | 목록 | share endpoint | - |

## DeletionRequest
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 삭제 요청 생성 | POST | `/deletion-requests` | 요청 생성 후 즉시 처리 시도 | Y | USER/ADMIN | Y | - | - | `application/json` | `DeletionRequestCreateRequest` | `201 DeletionRequestResponse` | `status=COMPLETED/FAILED` 가능 | `403 소유권`, `404` | 삭제 액션 결과 표시 | admin deletion | - |
| 삭제 요청 목록 | GET | `/deletion-requests` | 내 요청 목록 | Y | USER/ADMIN | Y | - | - | - | - | `200 DeletionRequestResponse[]` | 최신순 | `401` | 히스토리 | detail/cancel | - |
| 삭제 요청 상세 | GET | `/deletion-requests/{request_id}` | 내 요청 단건 | Y | USER/ADMIN | Y | `request_id` | - | - | - | `200 DeletionRequestResponse` | 상태/오류 | `403/404` | 상세 | cancel | - |
| 삭제 요청 취소 | PATCH | `/deletion-requests/{request_id}/cancel` | PENDING만 취소 | Y | USER/ADMIN | Y | `request_id` | - | - | - | `200 DeletionRequestResponse` | `status=CANCELLED` | `403 상태 불가`, `404` | 취소 버튼 | admin reject | `ACCOUNT 삭제는 TODO` |

## Report
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 신고 생성 | POST | `/reports` | 콘텐츠 신고 생성 | Y | USER/ADMIN | Y(작성자) | - | - | `application/json` | `CreateReportRequest` | `200 ReportResponse` | status=`PENDING` | `404 target 없음` | 신고 폼 | 사용자/관리자 보고서 조회 | **생성인데 201이 아닌 200** |
| 내 신고 목록 | GET | `/reports` | 내 신고 페이지 조회 | Y | USER/ADMIN | Y | - | `page,size` | - | - | `200 PaginatedResponse[ReportResponse]` | `items[]` | `422` | 목록 페이지 | detail | - |
| 내 신고 상세 | GET | `/reports/{report_id}` | 내 신고 단건 | Y | USER/ADMIN | Y | `report_id` | - | - | - | `200 ReportResponse` | 처리 상태 | `403/404` | 상세 | list | - |

## AuditLog / UsageLimit / RateLimit / Admin APIs
| 기능명 | Method | Path | 설명 | 인증 | Role | Owner-only | Path params | Query params | Req content-type | Req body/form | Success | 응답 필드 | 대표 에러/프론트 안내 | 프론트 화면/렌더링 | 관련 API | 확인 필요 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 검수요청 목록 | GET | `/admin/verification-requests` | 관리자 검수 목록 | Y | ADMIN | N | - | `status,page,size` | - | - | `200 PaginatedResponse[...]` | `items[]` | `422 status` | 관리자 검수 목록 | approve/reject/revoke | - |
| 검수요청 상세 | GET | `/admin/verification-requests/{request_id}` | 관리자 단건 조회 | Y | ADMIN | N | `request_id` | - | - | - | `200 VerificationRequestAdminResponse` | 심사 메타 | `404` | 상세 | file/patch | - |
| 검수 파일 다운로드 | GET | `/admin/verification-requests/{request_id}/file` | 보호 파일 반환 | Y | ADMIN | N | `request_id` | - | - | - | `200 file` | MIME/filename | `403 role`, `404` | 문서 미리보기 | verification APIs | - |
| 검수 승인 | PATCH | `/admin/verification-requests/{request_id}/approve` | 상태 APPROVED | Y | ADMIN | N | `request_id` | - | `application/json` | `VerificationRequestApproveRequest?` | `200 VerificationRequestAdminResponse` | reviewed fields | `422 상태` | 액션 버튼 | list/detail | - |
| 검수 반려 | PATCH | `/admin/verification-requests/{request_id}/reject` | 상태 REJECTED | Y | ADMIN | N | `request_id` | - | `application/json` | `VerificationRequestRejectRequest` | `200 VerificationRequestAdminResponse` | rejection_reason | `422` | 액션 버튼 | list/detail | - |
| 보완 요청 | PATCH | `/admin/verification-requests/{request_id}/need-more-info` | 상태 NEED_MORE_INFO | Y | ADMIN | N | `request_id` | - | `application/json` | `VerificationRequestNeedMoreInfoRequest` | `200 VerificationRequestAdminResponse` | admin_note | `422` | 액션 버튼 | list/detail | - |
| 승인 철회 | PATCH | `/admin/verification-requests/{request_id}/revoke` | 상태 REVOKED | Y | ADMIN | N | `request_id` | - | `application/json` | `VerificationRequestRevokeRequest?` | `200 VerificationRequestAdminResponse` | admin_note | `422` | 액션 버튼 | list/detail | - |
| 삭제요청 목록(admin) | GET | `/admin/deletion-requests` | 전체 삭제요청 조회 | Y | ADMIN | N | - | `status` | - | - | `200 DeletionRequestResponse[]` | 상태별 필터 | `422` | 운영 화면 | approve/reject | - |
| 삭제요청 상세(admin) | GET | `/admin/deletion-requests/{request_id}` | 단건 조회 | Y | ADMIN | N | `request_id` | - | - | - | `200 DeletionRequestResponse` | 요청/처리 정보 | `404` | 상세 | list | - |
| 삭제 승인/처리 | PATCH | `/admin/deletion-requests/{request_id}/approve-and-process` | 처리 실행 | Y | ADMIN | N | `request_id` | `admin_note` | - | - | `200 DeletionRequestResponse` | `status` 변경 | `403 상태` | 처리 버튼 | list/detail | - |
| 삭제 반려 | PATCH | `/admin/deletion-requests/{request_id}/reject` | 상태 REJECTED | Y | ADMIN | N | `request_id` | `admin_note` | - | - | `200 DeletionRequestResponse` | 처리 정보 | `403 상태` | 반려 버튼 | list/detail | - |
| 감사 로그 조회 | GET | `/admin/audit-logs` | 감사 로그 검색 | Y | ADMIN | N | - | `action,actor_user_id,target_type,target_id,start_date,end_date,page,size` | - | - | `200 PaginatedResponse[AuditLogResponse]` | `items[]` | `422 enum` | 감사 로그 화면 | - | - |
| 사용자 사용량 목록 | GET | `/admin/usage-limits` | 월별 사용자 사용량 | Y | ADMIN | N | - | `user_id,page,size` | - | - | `200 PaginatedResponse[UsageLimitResponse]` | remaining 포함 | `500` | 운영 대시보드 | update user limit | `user_id query가 현재 로직에서 미사용` |
| 사용자 사용량 수정 | PATCH | `/admin/users/{user_id}/usage-limit` | 사용자 한도 수정 | Y | ADMIN | N | `user_id` | - | `application/json` | `UpdateUsageLimitRequest` | `200 UsageLimitResponse` | 변경 반영값 | `500` | 운영 액션 | usage-limits | - |
| 페르소나 사용량 수정 | PATCH | `/admin/personas/{persona_id}/usage-limit` | 페르소나 한도 수정 | Y | ADMIN | N | `persona_id` | - | `application/json` | `UpdatePersonaUsageLimitRequest` | `200 PersonaUsageLimitResponse` | 변경 반영값 | `500` | 운영 액션 | rate limit | - |
| 레이트리밋 이벤트 조회 | GET | `/admin/rate-limit-events` | 이벤트 목록 | Y | ADMIN | N | - | `user_id,page,size` | - | - | `200 PaginatedResponse[RateLimitEventResponse]` | block/reason | `500` | 운영 모니터링 | usage-limits | - |
| 신고 목록(admin) | GET | `/admin/reports` | 전체 신고 조회 | Y | ADMIN | N | - | `status,page,size` | - | - | `200 PaginatedResponse` | 실제 items는 AdminReportResponse | `422 status` | 신고 관리 | 이하 report admin | **response_model 비구체** |
| 신고 상세(admin) | GET | `/admin/reports/{report_id}` | 단건 조회 | Y | ADMIN | N | `report_id` | - | - | - | `200 object` | AdminReportResponse 형태 | `404` | 상세 | status patch들 | **response_model 미지정** |
| 신고 reviewing | PATCH | `/admin/reports/{report_id}/reviewing` | 상태 REVIEWING | Y | ADMIN | N | `report_id` | - | `application/json` | `{admin_note?}` | `200 object` | AdminReportResponse 형태 | `404/400` | 액션 버튼 | detail/list | **request/response schema 미명시** |
| 신고 resolve | PATCH | `/admin/reports/{report_id}/resolve` | 상태 RESOLVED | Y | ADMIN | N | `report_id` | - | `application/json` | `{admin_note?}` | `200 object` | 동일 | `404` | 액션 버튼 | detail/list | **schema 미명시** |
| 신고 reject | PATCH | `/admin/reports/{report_id}/reject` | 상태 REJECTED | Y | ADMIN | N | `report_id` | - | `application/json` | `{admin_note?}` | `200 object` | 동일 | `404` | 액션 버튼 | detail/list | **schema 미명시** |
| 신고 action-taken | PATCH | `/admin/reports/{report_id}/action-taken` | 타겟 차단 조치 | Y | ADMIN | N | `report_id` | - | `application/json` | `{admin_note?}` | `200 object` | 동일 | `404` | 액션 버튼 | detail/list | **schema 미명시** |
| 보이스 프로필 상세(admin) | GET | `/admin/voice-profiles/{voice_profile_id}` | 음성 프로필 조회 | Y | ADMIN | N | `voice_profile_id` | - | - | - | `200 PersonaVoiceProfileResponse` | 상태/검수정보 | `404` | 검수 화면 | approve/reject/revoke | - |
| 보이스 프로필 승인(admin) | PATCH | `/admin/voice-profiles/{voice_profile_id}/approve` | READY 프로필 승인 | Y | ADMIN | N | `voice_profile_id` | - | `application/json` | `VoiceProfileReviewRequest` | `200 PersonaVoiceProfileResponse` | review_status | `400 READY 아님` | 검수 액션 | detail | - |
| 보이스 프로필 반려(admin) | PATCH | `/admin/voice-profiles/{voice_profile_id}/reject` | 프로필 반려 | Y | ADMIN | N | `voice_profile_id` | - | `application/json` | `VoiceProfileReviewRequest` | `200 PersonaVoiceProfileResponse` | status FAILED | `404` | 검수 액션 | detail | - |
| 보이스 프로필 철회(admin) | PATCH | `/admin/voice-profiles/{voice_profile_id}/revoke` | 사용 철회 | Y | ADMIN | N | `voice_profile_id` | - | `application/json` | `VoiceProfileReviewRequest` | `200 PersonaVoiceProfileResponse` | status REVOKED | `404` | 검수 액션 | detail | - |

## VoiceCall WebSocket
| 항목 | 내용 |
| --- | --- |
| endpoint | `WS /api/v1/ws/personas/{persona_id}/voice?token=<access_token>` |
| 연결 전 조건 | 유효 access token, persona 소유권, voice clone 사용 가능(검증 승인 + 동의 + READY/review 상태), 호출량 제한 통과 |
| 클라이언트 메시지 타입 | `start`, `audio_chunk`, `end_utterance`, `stop` |
| `start` payload | `{ "type": "start", "chat_id": optional<int> }` |
| `audio_chunk` payload | `{ "type": "audio_chunk", "data": "<base64>", "mime_type": "audio/webm|audio/wav|audio/mpeg|audio/mp4" }` |
| `end_utterance` payload | `{ "type": "end_utterance" }` |
| `stop` payload | `{ "type": "stop" }` |
| 서버 메시지 타입 | `session_started`, `final_transcript`, `persona_text`, `persona_audio`, `session_ended`, `error` |
| `persona_audio` payload | `{ "type":"persona_audio", "audio_url": "...", "audio_file_path": "..." }` |
| 세션 라이프사이클 | `start` -> N회 `audio_chunk` -> `end_utterance` 반복 -> `stop` 종료 |
| 에러 이벤트 | `{ "type":"error", "message":"..." }` |
| 프론트 렌더링 가이드 | 연결 실패/에러 시 재시도 버튼 제공, `session_started` 전에는 chunk 전송 금지, `persona_audio`는 보호 파일 정책과의 정합성 확인 필요 |
| 확인 필요 | `persona_audio.audio_url`가 `/uploads/...` 기반 경로를 반환할 수 있어 운영에서 public static 비활성 시 직접 재생 불가 가능성 있음 |

## Persona 생성 전 Gate Flow (코드 기준)
1. Target 소유권 확인
2. Target verification 승인 상태 확인 (`APPROVED`, 만료 전)
3. `ai_persona_creation_consent`, `ai_response_notice_consent` 확인
4. 이미지가 있으면 `photo_upload_consent` 확인
5. 음성이 있으면 `voice_upload_consent` + `voice_cloning_consent` + voice profile 생성 허용 조건 확인

프론트 안내 문구 예시:
- `Target verification approval is required before creating persona.`
- 프론트 안내: 관계 입증이 승인된 뒤 페르소나를 만들 수 있어요.

## OpenAPI와 코드 불일치 요약
- `/admin/reports*` 일부 endpoint는 `response_model`이 구체적으로 지정되지 않아 Swagger 스키마가 약함
- `POST /reports`는 생성 API지만 status code가 `200`
- `realtime voice`는 OpenAPI 자동 문서 밖
- `StoryVoiceNarration` 관련 HTTP endpoint 없음 (모델만 존재)
## Usage Limit Migration Note (2026-05-14)
- Missing tables issue was fixed by Alembic revision `c8f1d4a7b9e2` (down_revision: `a4c8e2f1b9d0`).
- This revision creates `usage_limits`, `persona_usage_limits`, and `rate_limit_events`.
- Model-aligned unique indexes:
  - `ix_usage_limits_user_ym` (`user_id`, `period_ym`)
  - `ix_persona_usage_limits_persona_ym` (`persona_id`, `period_ym`)
- `GET /admin/usage-limits?user_id={id}` now lazily creates the current month row when missing.
- `PATCH /admin/users/{user_id}/usage-limit` and `PATCH /admin/personas/{persona_id}/usage-limit` also create missing current month rows before update.
- `period_ym` format is `YYYY-MM`.
- DB internal errors are returned with safe messages, not raw SQL text.
