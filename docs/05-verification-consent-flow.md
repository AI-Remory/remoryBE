# 05. Verification Consent Flow

## 목차

- [목적](#목적)
- [Target Verification](#target-verification)
- [Consent Log](#consent-log)
- [Persona 생성 조건](#persona-생성-조건)
- [Voice Profile 조건](#voice-profile-조건)
- [Admin 검수](#admin-검수)
- [프론트 상태 정책](#프론트-상태-정책)

## 목적

Target 기반 persona와 음성 기능은 target 검증, 동의 로그, media/voice sample 상태에 영향을 받는다. 이 문서는 실제 모델, 라우터, 서비스 기준으로 프론트가 어떤 상태를 보여야 하는지 정리한다.

## Target Verification

사용자 API:

| API | 설명 |
| --- | --- |
| `POST /api/v1/targets/{target_id}/verification-requests` | multipart 검증 파일 제출 |
| `GET /api/v1/targets/{target_id}/verification-requests` | target별 내 검증 요청 목록 |
| `GET /api/v1/verification-requests/{request_id}` | 검증 요청 상세 |

`VerificationStatus`:

| 값 | 의미 |
| --- | --- |
| `PENDING` | 제출 후 admin 검수 대기 |
| `NEED_MORE_INFO` | admin이 추가 정보 요청 |
| `APPROVED` | 승인됨 |
| `REJECTED` | 거절됨 |
| `EXPIRED` | 만료됨 |
| `REVOKED` | 철회됨 |

`VerificationType`은 `FAMILY_RELATION_CERTIFICATE`, `ID_CARD`, `SELF_DECLARATION`, `OTHER`다. 생성 request는 `verification_type_param`, `applicant_note`, `file`을 multipart form으로 보낸다.

## Consent Log

사용자 API:

| API | 설명 |
| --- | --- |
| `POST /api/v1/consents` | 동의 로그 생성 |
| `GET /api/v1/consents` | 내 동의 목록 |
| `GET /api/v1/targets/{target_id}/consents` | target별 동의 목록 |
| `PATCH /api/v1/consents/{consent_id}/revoke` | 동의 철회 |

`ConsentType`은 현재 코드에서 다음 값을 허용한다.

| 목적 | 값 |
| --- | --- |
| Target profile | `target_profile_consent` |
| Photo upload | `photo_upload_consent` |
| Voice upload | `voice_upload_consent` |
| Voice cloning | `voice_cloning_consent` |
| AI persona | `ai_persona_creation_consent` |
| AI response notice | `ai_response_notice_consent` |
| Storybook share | `storybook_share_consent` |
| Group share | `group_share_consent` |
| Data retention | `data_retention_consent` |
| Third-party AI | `third_party_ai_processing_consent` |
| Legacy | `voice_collection`, `photo_collection`, `persona_creation`, `data_usage`, `ai_processing`, `ai_response_notice`, `storybook_share` |

## Persona 생성 조건

실제 endpoint는 `POST /api/v1/targets/{target_id}/persona`다. 서비스 레이어는 target owner, target 검증 상태, consent/media 조건을 확인한다.

프론트는 persona 생성 전 다음 상태를 확인해 안내한다.

| 조건 | 확인 API |
| --- | --- |
| target 존재/소유 | `GET /api/v1/targets/{target_id}` |
| 검증 승인 여부 | `GET /api/v1/targets/{target_id}/verification-requests` |
| 동의 여부 | `GET /api/v1/targets/{target_id}/consents` |
| media 존재 여부 | `GET /api/v1/targets/{target_id}/media` |

성공 응답은 `PersonaDetailResponse`다. `is_consent_required`가 true이면 필요한 동의를 UI에서 추가로 유도한다.

## Voice Profile 조건

Voice profile API:

| API | 설명 |
| --- | --- |
| `POST /api/v1/personas/{persona_id}/voice-profile` | voice sample 기반 profile 생성 |
| `GET /api/v1/personas/{persona_id}/voice-profile` | profile 조회 |
| `POST /api/v1/personas/{persona_id}/voice-profile/evaluate` | 품질 평가 |
| `PATCH /api/v1/personas/{persona_id}/voice-profile/user-confirm` | 사용자 확인 |

`Settings` 기준 voice 품질 조건:

| 설정 | 기본값 |
| --- | --- |
| `VOICE_SAMPLE_MIN_COUNT` | `1` |
| `VOICE_SAMPLE_MIN_TOTAL_DURATION_MS` | `100` |
| `VOICE_SAMPLE_MIN_FILE_SIZE_BYTES` | `1024` |
| `VOICE_PROFILE_MIN_QUALITY_SCORE` | `0.5` |

`VoiceProfileStatus`: `PENDING`, `PROCESSING`, `READY`, `FAILED`, `NEEDS_MORE_SAMPLES`, `REVOKED`.

`VoiceProfileReviewStatus`: `NOT_REVIEWED`, `USER_CONFIRMED`, `ADMIN_APPROVED`, `REJECTED`.

## Admin 검수

Admin verification:

| API | 설명 |
| --- | --- |
| `GET /api/v1/admin/verification-requests` | 검증 요청 목록 |
| `GET /api/v1/admin/verification-requests/{request_id}` | 상세 |
| `GET /api/v1/admin/verification-requests/{request_id}/file` | 제출 파일 |
| `PATCH /api/v1/admin/verification-requests/{request_id}/approve` | 승인 |
| `PATCH /api/v1/admin/verification-requests/{request_id}/reject` | 거절 |
| `PATCH /api/v1/admin/verification-requests/{request_id}/need-more-info` | 추가 정보 요청 |
| `PATCH /api/v1/admin/verification-requests/{request_id}/revoke` | 승인 철회 |

Admin voice profile:

| API | 설명 |
| --- | --- |
| `GET /api/v1/admin/voice-profiles/{voice_profile_id}` | voice profile 조회 |
| `PATCH /api/v1/admin/voice-profiles/{voice_profile_id}/approve` | 승인 |
| `PATCH /api/v1/admin/voice-profiles/{voice_profile_id}/reject` | 거절 |
| `PATCH /api/v1/admin/voice-profiles/{voice_profile_id}/revoke` | 철회 |

## 프론트 상태 정책

| 상태 | UI |
| --- | --- |
| 검증 요청 없음 | 검증 제출 CTA |
| `PENDING` | 검수 대기 배지 |
| `NEED_MORE_INFO` | admin note 확인 후 재제출 안내 |
| `APPROVED` | persona/voice 기능 unlock |
| `REJECTED` | rejection reason 표시 |
| `REVOKED`/`EXPIRED` | 재검증 CTA |
| voice profile `NEEDS_MORE_SAMPLES` | voice sample 추가 업로드 안내 |
| voice profile `READY` + `USER_CONFIRMED`/`ADMIN_APPROVED` | 음성 대화 활성화 |
