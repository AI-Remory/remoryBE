# 05. Verification Consent Flow

## 목차

- [목적](#목적)
- [TargetVerificationRequest 흐름](#targetverificationrequest-흐름)
- [ConsentLog 흐름](#consentlog-흐름)
- [Persona 생성 전 검증 조건](#persona-생성-전-검증-조건)
- [Voice Cloning 허용 조건](#voice-cloning-허용-조건)
- [프론트 상태 정책](#프론트-상태-정책)
- [보안 정책](#보안-정책)

## 목적

Remory는 사진, 음성, 사적 기억을 다룬다. 따라서 "이 target을 내가 다뤄도 되는가"와 "이 데이터를 특정 목적으로 사용해도 되는가"를 분리해 검증한다.

- `TargetVerificationRequest`: 관계/권한 검증
- `ConsentLog`: 목적별 데이터 사용 동의

Persona 생성과 voice cloning은 두 조건을 모두 만족해야 한다.

## TargetVerificationRequest 흐름

```text
Target 생성
  -> Verification 문서 제출
  -> PENDING
  -> Admin review
  -> APPROVED / REJECTED / NEED_MORE_INFO / REVOKED
  -> APPROVED일 때 persona/voice policy gate 통과 가능
```

주요 상태:

| Status | 의미 | Persona 생성 |
| --- | --- | --- |
| `PENDING` | 제출 후 검토 대기 | 불가 |
| `NEED_MORE_INFO` | 추가 자료 필요 | 불가 |
| `APPROVED` | 관계/권한 승인 | 가능 |
| `REJECTED` | 거절 | 불가 |
| `EXPIRED` | 승인 만료 | 불가 |
| `REVOKED` | 승인 철회 | 불가 |

Verification type:

- `FAMILY_RELATION_CERTIFICATE`
- `ID_CARD`
- `SELF_DECLARATION`
- `OTHER`

파일 정책:

- 파일은 기존 로컬 `uploads/verifications/{user_id}/` 구조에 저장한다.
- 일반 사용자 JSON 응답에는 내부 파일 경로를 포함하지 않는다.
- admin만 `GET /api/v1/admin/verification-requests/{request_id}/file`로 권한 확인 후 파일을 조회한다.

## ConsentLog 흐름

Consent는 append-only history로 저장한다. 최신 row가 현재 상태다.

```text
POST /api/v1/consents
  -> is_agreed=true
  -> agreed_at 기록

PATCH /api/v1/consents/{consent_id}/revoke
  -> is_agreed=false
  -> is_consented=false
  -> revoked_at 기록
```

권장 consent type:

| 목적 | consent_type |
| --- | --- |
| Target profile data | `target_profile_consent` |
| Photo upload | `photo_upload_consent` |
| Voice upload | `voice_upload_consent` |
| Voice cloning | `voice_cloning_consent` |
| AI persona creation | `ai_persona_creation_consent` |
| AI response notice | `ai_response_notice_consent` |
| StoryBook share link | `storybook_share_consent` |
| Group share | `group_share_consent` |
| Data retention | `data_retention_consent` |
| Third-party AI processing | `third_party_ai_processing_consent` |

Legacy consent 값은 호환을 위해 일부 fallback된다. 신규 프론트 코드는 granular consent type을 사용한다.

## Persona 생성 전 검증 조건

`POST /api/v1/targets/{target_id}/persona`는 다음 조건이 필요하다.

1. 로그인 사용자가 target owner여야 한다.
2. target이 삭제되지 않아야 한다.
3. target에 `APPROVED` verification이 있어야 한다.
4. 만료된 approval은 유효하지 않다.
5. `ai_persona_creation_consent`가 active여야 한다.
6. `ai_response_notice_consent`가 active여야 한다.
7. photo media가 있으면 `photo_upload_consent`가 active여야 한다.
8. voice media가 있으면 `voice_upload_consent`와 `voice_cloning_consent`가 active여야 한다.

조건 미충족 시 일반적으로 `403`이 반환된다.

## Voice Cloning 허용 조건

Voice cloning 또는 voice profile 사용은 persona 생성보다 더 엄격하다.

필수 조건:

1. 로그인 사용자가 persona owner여야 한다.
2. persona target에 `APPROVED` verification이 있어야 한다.
3. `voice_upload_consent`가 active여야 한다.
4. `voice_cloning_consent`가 active여야 한다.
5. target voice media가 하나 이상 있어야 한다.
6. `PersonaVoiceProfile.status == READY`
7. `PersonaVoiceProfile.review_status`가 `USER_CONFIRMED` 또는 `ADMIN_APPROVED`여야 한다.
8. profile이 삭제되거나 revoked 상태가 아니어야 한다.

Realtime voice chat도 이 gate를 사용한다.

## 프론트 상태 정책

권장 UI:

- verification `PENDING`: "검토 중" 표시, persona 생성 버튼 비활성화
- verification `APPROVED`: persona 생성 버튼 활성화
- verification `REJECTED`: 거절 사유 표시, 재제출 유도
- consent missing: 해당 체크박스/동의 화면으로 이동
- voice profile `READY` 전: 음성 합성/통화 버튼 비활성화
- voice profile `READY`지만 review 미확인: 사용자 확인 버튼 표시

프론트는 상태를 미리 표시하되, 최종 정책 판단은 항상 서버 응답을 따른다.

## 보안 정책

- 민감 verification 파일 경로는 사용자 응답에 노출하지 않는다.
- voice cloning은 명시 동의와 검증 승인 없이는 허용하지 않는다.
- 삭제 요청 시 실제 파일 삭제와 metadata 정리를 함께 고려한다.
- AuditLog에는 민감 secret/token/password를 저장하지 않는다.
- share link 공개 화면은 읽기 전용이며 owner 내부 정보 노출을 피한다.
