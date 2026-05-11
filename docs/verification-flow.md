# Target Verification Flow

이 문서는 Remory의 **Target Verification** 기능이 왜 필요한지, 사용자/관리자/페르소나 생성 흐름이 어떻게 연결되는지, 그리고 프론트엔드와 백엔드가 어떤 정책을 공통 기준으로 구현해야 하는지를 정리한다.

---

## 1. 목적

Target Verification은 다음과 같은 문제를 줄이기 위한 안전장치다.

- 타인의 음성/사진을 무단으로 이용해 페르소나를 생성하는 행위 방지
- Voice Cloning 도입 전, 관계 입증과 관리자 승인을 거치도록 보장
- `ConsentLog`와 함께 동작하여, 데이터 사용 동의와 관계 확인을 모두 만족해야만 민감 기능이 동작하도록 함

즉, **"이 target을 내가 다루어도 되는가?"**와 **"이 target의 데이터를 이 용도로 사용해도 되는가?"**를 분리해서 검증하는 구조다.

---

## 2. 전체 흐름

아래 흐름은 현재 구현된 정책을 기준으로 하며, 프론트엔드와 백엔드는 동일한 기준을 사용해야 한다.

1. 사용자가 `Target`을 생성한다.
2. 사용자가 관계 입증 문서를 업로드해 `TargetVerificationRequest`를 생성한다.
3. 요청 상태는 `PENDING`으로 저장된다.
4. 관리자가 요청 문서를 검토한다.
5. 관리자는 요청을 `APPROVED` 또는 `REJECTED`로 처리한다.
6. `APPROVED` 상태일 때만 Persona 생성이 가능하다.
7. 추후 Voice Cloning도 동일하게 `APPROVED` 상태에서만 허용하도록 확장한다.

간단히 표현하면 다음과 같다.

```text
Target 생성
→ Verification 문서 업로드
→ PENDING
→ 관리자 검토
→ APPROVED / REJECTED
→ APPROVED일 때 Persona 생성 가능
→ Voice Cloning도 동일 원칙으로 확장 예정
```

---

## 3. 상태 정의

`TargetVerificationRequest.status`는 다음 상태를 가진다.

### PENDING
- 사용자가 입증 문서를 제출한 직후 상태
- 아직 관리자 검토가 완료되지 않음
- 프론트에서는 "심사 중"으로 표시

### APPROVED
- 관리자가 관계 입증을 승인한 상태
- Persona 생성 가능
- 이후 Voice Cloning 같은 민감 기능 확장 시에도 허용 조건으로 사용

### REJECTED
- 관리자가 관계 입증을 거절한 상태
- 프론트에서는 거절 사유를 보여주고 재제출을 유도

---

## 4. verification_type 정의

`TargetVerificationRequest.verification_type`은 관계 입증 문서의 유형을 나타낸다.

- `FAMILY_RELATION_CERTIFICATE`
- `ID_CARD`
- `SELF_DECLARATION`
- `OTHER`

### 사용 의도
- `FAMILY_RELATION_CERTIFICATE`: 가족관계증명서 등 공식 관계 증빙
- `ID_CARD`: 신분증 기반 확인
- `SELF_DECLARATION`: 자가 진술서/동의서 등
- `OTHER`: 기타 문서

프론트엔드에서는 드롭다운 또는 라디오 버튼으로 이 값을 선택하게 구현할 수 있다.

---

## 5. 사용자 화면 정책

사용자 화면에서는 verification 상태에 따라 CTA와 설명을 명확히 분리해야 한다.

### PENDING
- 상태 텍스트: `심사 중`
- Persona 생성 버튼: 비활성화
- 안내 문구: "관리자 검토를 기다리고 있습니다."

### APPROVED
- 상태 텍스트: `승인 완료`
- Persona 생성 버튼: 활성화
- 다음 단계 진행 가능

### REJECTED
- 상태 텍스트: `거절됨`
- `rejection_reason`을 사용자에게 표시
- 재제출 유도 문구 제공
- Persona 생성 버튼: 비활성화

### UX 권장사항
- 상태는 색상만으로 구분하지 말고 텍스트도 함께 표시
- 거절 사유는 가능한 한 명확하고 읽기 쉬운 형태로 보여줄 것
- 승인 전에는 Persona 생성 버튼을 숨기거나 비활성화하는 것이 좋음

---

## 6. 관리자 화면 정책

관리자 화면은 검토 업무가 빠르고 정확하게 이루어지도록 설계해야 한다.

### 목록 기본 정책
- `PENDING` 요청을 우선적으로 보여준다.
- 필요 시 `APPROVED`, `REJECTED` 필터로 전환 가능해야 한다.
- 제출일이 최근인 요청을 먼저 확인하는 흐름이 적합하다.

### 문서 확인
- 업로드된 입증 문서를 확인한다.
- 내부 파일 경로나 저장 경로를 관리자 화면에 직접 노출할 필요는 없다.
- 문서 조회는 권한이 있는 관리자 흐름 안에서만 처리한다.

### 승인/거절
- 승인 시 상태를 `APPROVED`로 변경한다.
- 거절 시 상태를 `REJECTED`로 변경한다.
- 거절 시 `rejection_reason`은 필수다.

### 검토 시 기록
관리자는 다음 정보가 기록되도록 처리해야 한다.

- `reviewed_by`
- `reviewed_at`
- `rejection_reason`(거절 시)

---

## 7. Persona 생성 정책

Persona 생성은 다음 순서를 따라야 한다.

1. target 소유자인지 확인
2. verification이 `APPROVED`인지 확인
3. 필요한 `ConsentLog`가 존재하는지 확인
4. Persona 생성

### 정책 의미
- **target 소유자 확인**: 본인이 관리하는 target인지 검증
- **verification APPROVED 확인**: 관계 입증이 승인되었는지 검증
- **ConsentLog 확인**: 데이터 사용 동의가 존재하는지 검증
- **persona 생성**: 위 조건을 모두 만족할 때만 실행

이 순서는 프론트와 백엔드가 동일하게 이해해야 하는 핵심 정책이다.

---

## 8. Voice Cloning 확장 정책

현재는 Persona 생성 중심이지만, 향후 Voice Cloning 기능도 같은 안전 원칙을 따라야 한다.

### Voice Cloning 허용 조건
- verification이 `APPROVED`여야 함
- voice cloning에 대한 `ConsentLog`가 필요함
- target에 voice media가 존재해야 함
- AI 생성 음성이라는 점을 사용자에게 명확히 고지해야 함

### 추가 고려사항
- 음성 데이터는 얼굴 사진보다 더 민감할 수 있으므로 더 엄격하게 다뤄야 함
- 재생성/재사용 범위가 명확해야 함
- 저장 및 삭제 정책이 분리되어야 함

---

## 9. 보안 주의사항

Target Verification은 민감 문서를 다루므로 프론트와 백엔드 모두 신중한 처리가 필요하다.

### 민감 문서 관리
- 가족관계증명서, 신분증 등 민감 정보는 매우 조심해서 다룬다.
- 파일명, 저장 위치, 내부 경로를 사용자에게 직접 보여주지 않는다.

### 내부 파일 경로 노출 금지
- 사용자 화면에는 `document_file_path` 같은 내부 저장 경로를 노출하지 않는다.
- 필요한 경우에도 서버가 권한 체크를 거친 별도 다운로드/조회 흐름을 제공해야 한다.

### 안전한 저장소 권장
실서비스에서는 다음과 같은 구성을 권장한다.

- S3 private bucket
- 접근 제어가 적용된 별도 보안 저장소
- 서버 측 서명 URL 또는 권한 검증 기반 파일 제공

### 삭제 요청 시 파일 정책
삭제 요청이 발생하면 다음을 고려해야 한다.

- 원본 파일을 즉시 삭제할지
- 일정 기간 보관 후 비식별 처리할지
- 백업/아카이브 정책과 충돌하지 않는지

이 정책은 개인정보 보호와 감사 요구사항을 함께 고려해 정해야 한다.

### 권장: Verification 문서 삭제/보존 정책 (권장안)

권장 정책은 민감 문서(신분증, 가족관계증명서 등)는 즉시 원본 파일을 삭제하되, 서비스 운영과
감사를 위해 필요한 최소한의 메타데이터만 보관하는 것입니다. 구체적으로 권장되는 처리 항목은 다음과 같습니다.

- 즉시 삭제할 항목:
  - 실제 document file (스토리지의 파일)
  - 내부 저장 경로 (`document_file_path`) → null 처리
  - 내부 저장 파일명 (`stored_filename`) → null 처리
  - MIME 타입/파일 크기 등 파일 식별/메타 정보 → null 처리

- 보관(유지)할 항목 (운영/감사용 최소 메타데이터):
  - id, user_id, target_id, verification_type, status
  - submitted_at, reviewed_at, reviewed_by, rejection_reason
  - created_at, updated_at, deleted_at (레코드 비활성화/감사용)

- 선택 항목:
  - original_filename은 사용자의 편의 및 운영 목적으로 남길 수 있으나 민감할 수 있으므로
	서비스 정책에 따라 삭제할 수 있습니다. (MVP에서는 보존)

운영 권장사항:

- 사용자 조회 API에서는 내부 경로/저장파일명 등의 민감 필드를 응답에 포함시키지 마세요.
- 관리자는 별도 권한 있는 조회/다운로드 경로를 통해 문서를 확인해야 하며, UI에 내부 경로를
  직접 노출하지 않도록 합니다.
- include_deleted 옵션을 통해 추후 감사용으로 삭제된 항목을 조회할 수 있도록 확장할 수
  있으나, MVP에서는 기본적으로 삭제된 레코드는 목록에서 제외합니다.

---

## 10. 프론트/백엔드 공통 합의 포인트

프론트엔드와 백엔드는 다음 기준을 동일하게 유지해야 한다.

- verification 미승인 상태에서는 Persona 생성 불가
- 거절된 verification은 거절 사유를 사용자에게 보여줘야 함
- 관리자 승인/거절은 `PENDING` 요청 중심으로 처리
- `APPROVED`가 되어야만 Persona 생성 및 향후 Voice Cloning이 가능
- 민감 문서의 내부 저장 경로는 UI에 노출하지 않음

---

## 11. 권장 구현 순서

### 사용자 화면
1. Target 생성
2. Verification 문서 업로드
3. 상태 표시 컴포넌트 구현
4. 승인 전 Persona 생성 버튼 비활성화
5. 거절 사유 표시 및 재제출 유도

### 관리자 화면
1. `PENDING` 목록 페이지 구현
2. 문서 검토 화면 구현
3. 승인/거절 액션 연결
4. 거절 사유 입력 validation 적용

### 정책 점검
1. Persona 생성 전에 verification 승인 확인
2. ConsentLog 검증 확인
3. Voice Cloning 확장 정책 문서화
4. 파일 보안 정책 점검

---

## 12. 요약

Target Verification은 Remory에서 **민감한 데이터 사용의 첫 번째 안전장치**다.

- 관계 입증이 있어야 한다.
- 관리자 승인이 있어야 한다.
- ConsentLog가 함께 있어야 한다.
- 승인된 대상만 Persona 생성이 가능하다.
- 향후 Voice Cloning도 같은 원칙으로 확장한다.

이 문서는 프론트엔드와 백엔드가 같은 정책을 바라보고 구현하기 위한 기준 문서다.

