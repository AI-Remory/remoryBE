"""Target Verification Tests"""


def _create_target(client, headers, name):
    response = client.post(
        "/api/v1/targets",
        json={"name": name, "description": f"{name} description", "target_type": "parent"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def _create_verification_request(client, headers, target_id, verification_type="family_relation_certificate"):
    response = client.post(
        f"/api/v1/targets/{target_id}/verification-requests",
        data={"verification_type_param": verification_type},
        files={"file": (f"{verification_type}.pdf", b"fake pdf content", "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def _approve_verification_request(client, headers, request_id):
    response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/approve",
        json={},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def _reject_verification_request(client, headers, request_id, reason):
    response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/reject",
        json={"rejection_reason": reason},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_create_verification_request_own_target(client, auth_headers, created_target):
    """본인 target에 입증 요청 생성 성공"""
    response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "family_relation_certificate"},
        files={"file": ("cert.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == created_target["user_id"]
    assert data["target_id"] == created_target["id"]
    assert data["verification_type"] == "FAMILY_RELATION_CERTIFICATE"
    assert data["status"] == "PENDING"
    assert data["original_filename"] == "cert.pdf"
    assert data["mime_type"] == "application/pdf"
    # 내부 저장 경로나 저장파일명은 응답에 노출되지 않아야 함
    assert "submitted_file_path" not in data
    assert "document_file_path" not in data
    assert "stored_filename" not in data


def test_create_verification_request_other_user_target(client, auth_headers, second_user_headers, created_target):
    """다른 사용자 target에 입증 요청 생성 실패"""
    response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "family_relation_certificate"},
        files={"file": ("cert.pdf", b"fake pdf content", "application/pdf")},
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)


def test_get_user_verification_requests(client, auth_headers, created_target):
    """사용자의 입증 요청 목록 조회"""
    # 요청 생성
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "id_card"},
        files={"file": ("id.jpg", b"fake image content", "image/jpeg")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    # 목록 조회
    response = client.get(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "PENDING"
    # 목록 응답에 내부 파일 경로나 저장파일명은 포함되지 않음
    assert "submitted_file_path" not in data["items"][0]
    assert "document_file_path" not in data["items"][0]
    assert "stored_filename" not in data["items"][0]


def test_get_verification_request_detail(client, auth_headers, created_target):
    """입증 요청 상세 조회"""
    # 요청 생성
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "self_declaration"},
        files={"file": ("decl.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    # 상세 조회
    response = client.get(
        f"/api/v1/verification-requests/{request_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == request_id
    assert data["status"] == "PENDING"
    # 상세 응답에도 내부 파일 경로나 저장파일명은 포함되지 않음
    assert "submitted_file_path" not in data
    assert "document_file_path" not in data
    assert "stored_filename" not in data


def test_list_verification_requests_admin(client, auth_headers, admin_headers):
    """관리자가 verification 요청 전체 목록을 조회한다."""
    pending_target = _create_target(client, auth_headers, "Pending Target")
    approved_target = _create_target(client, auth_headers, "Approved Target")
    rejected_target = _create_target(client, auth_headers, "Rejected Target")

    pending_request = _create_verification_request(client, auth_headers, pending_target["id"])
    approved_request = _create_verification_request(client, auth_headers, approved_target["id"], "id_card")
    rejected_request = _create_verification_request(client, auth_headers, rejected_target["id"], "other")

    _approve_verification_request(client, admin_headers, approved_request["id"])
    _reject_verification_request(
        client,
        admin_headers,
        rejected_request["id"],
        "Document is not clear and needs higher quality image",
    )

    response = client.get("/api/v1/admin/verification-requests", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert [item["id"] for item in data["items"]] == [rejected_request["id"], approved_request["id"], pending_request["id"]]
    assert {item["status"] for item in data["items"]} == {"PENDING", "APPROVED", "REJECTED"}
    assert all("submitted_file_path" not in item for item in data["items"])
    assert all("document_file_path" not in item for item in data["items"])


def test_list_pending_requests_admin(client, auth_headers, admin_headers):
    """status=PENDING 필터 조회"""
    pending_target = _create_target(client, auth_headers, "Pending Filter Target")
    approved_target = _create_target(client, auth_headers, "Approved Filter Target")

    pending_request = _create_verification_request(client, auth_headers, pending_target["id"])
    approved_request = _create_verification_request(client, auth_headers, approved_target["id"], "id_card")
    _approve_verification_request(client, admin_headers, approved_request["id"])

    response = client.get("/api/v1/admin/verification-requests?status=PENDING", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == pending_request["id"]
    assert data["items"][0]["status"] == "PENDING"


def test_list_approved_requests_admin(client, auth_headers, admin_headers):
    """status=APPROVED 필터 조회"""
    approved_target = _create_target(client, auth_headers, "Approved Only Target")
    pending_target = _create_target(client, auth_headers, "Pending Only Target")

    approved_request = _create_verification_request(client, auth_headers, approved_target["id"], "id_card")
    _approve_verification_request(client, admin_headers, approved_request["id"])
    _create_verification_request(client, auth_headers, pending_target["id"])

    response = client.get("/api/v1/admin/verification-requests?status=APPROVED", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == approved_request["id"]
    assert data["items"][0]["status"] == "APPROVED"


def test_list_verification_requests_pagination(client, auth_headers, admin_headers):
    """page/size pagination 조회"""
    first_target = _create_target(client, auth_headers, "Pagination Target 1")
    second_target = _create_target(client, auth_headers, "Pagination Target 2")
    third_target = _create_target(client, auth_headers, "Pagination Target 3")

    first_request = _create_verification_request(client, auth_headers, first_target["id"])
    second_request = _create_verification_request(client, auth_headers, second_target["id"])
    _create_verification_request(client, auth_headers, third_target["id"])

    response = client.get("/api/v1/admin/verification-requests?page=2&size=1", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["skip"] == 1
    assert data["limit"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == second_request["id"]


def test_approve_verification_request(client, auth_headers, admin_headers, created_target):
    """입증 요청 승인"""
    # 요청 생성
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "id_card"},
        files={"file": ("id.jpg", b"fake image content", "image/jpeg")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    # 관리자가 승인
    response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/approve",
        json={},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["reviewed_by"] is not None
    assert data["reviewed_at"] is not None


def test_approve_verification_records_admin_and_clears_rejection_reason(client, auth_headers, admin_headers, admin_user, created_target):
    """승인 시 reviewed_by / reviewed_at 이 관리자 기준으로 저장되고 rejection_reason 이 제거된다."""
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "id_card"},
        files={"file": ("id.jpg", b"fake image content", "image/jpeg")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/approve",
        json={},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reviewed_by"] == admin_user.id
    assert data["reviewed_at"] is not None
    assert data["rejection_reason"] is None


def test_reject_verification_request(client, auth_headers, admin_headers, created_target):
    """입증 요청 거절"""
    # 요청 생성
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "other"},
        files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    # 관리자가 거절
    response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/reject",
        json={"rejection_reason": "Document is not clear and needs higher quality image"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
    assert data["reviewed_by"] is not None
    assert data["rejection_reason"] == "Document is not clear and needs higher quality image"


def test_need_more_info_verification_request(client, auth_headers, admin_headers, created_target):
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "other"},
        files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    response = client.patch(
        f"/api/v1/admin/verification-requests/{create_response.json()['id']}/need-more-info",
        json={"admin_note": "Please upload a clearer document"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NEED_MORE_INFO"
    assert data["admin_note"] == "Please upload a clearer document"


def test_revoke_verification_request(client, auth_headers, admin_headers, created_target):
    request = _create_verification_request(client, auth_headers, created_target["id"], "id_card")
    _approve_verification_request(client, admin_headers, request["id"])

    response = client.patch(
        f"/api/v1/admin/verification-requests/{request['id']}/revoke",
        json={"admin_note": "Approval revoked after manual review"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REVOKED"
    assert data["admin_note"] == "Approval revoked after manual review"


def test_admin_get_verification_request_detail(client, auth_headers, admin_headers, created_target):
    request = _create_verification_request(client, auth_headers, created_target["id"], "id_card")

    response = client.get(
        f"/api/v1/admin/verification-requests/{request['id']}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == request["id"]
    assert "submitted_file_path" not in data


def test_admin_verification_file_requires_admin(client, auth_headers, admin_headers, created_target):
    request = _create_verification_request(client, auth_headers, created_target["id"], "id_card")

    user_response = client.get(
        f"/api/v1/admin/verification-requests/{request['id']}/file",
        headers=auth_headers,
    )
    assert user_response.status_code == 403

    admin_response = client.get(
        f"/api/v1/admin/verification-requests/{request['id']}/file",
        headers=admin_headers,
    )
    assert admin_response.status_code == 200
    assert admin_response.content == b"fake pdf content"


def test_reject_verification_records_admin_and_reason(client, auth_headers, admin_headers, admin_user, created_target):
    """거절 시 reviewed_by / reviewed_at / rejection_reason 이 저장된다."""
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "other"},
        files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    reason = "Document is not clear and needs higher quality image"
    response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/reject",
        json={"rejection_reason": reason},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reviewed_by"] == admin_user.id
    assert data["reviewed_at"] is not None
    assert data["rejection_reason"] == reason


def test_reject_verification_requires_non_empty_reason(client, admin_headers, created_target, auth_headers):
    """빈 거절 사유는 validation 에러가 나야 한다."""
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "other"},
        files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/reject",
        json={"rejection_reason": ""},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_reject_verification_too_long_reason_rejected(client, admin_headers, created_target, auth_headers):
    """너무 긴 거절 사유는 validation 에러가 나야 한다."""
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "other"},
        files={"file": ("doc.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/reject",
        json={"rejection_reason": "x" * 501},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_general_user_cannot_approve_or_reject(client, auth_headers, created_target):
    """일반 사용자는 승인/거절 API를 사용할 수 없다."""
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "id_card"},
        files={"file": ("id.jpg", b"fake image content", "image/jpeg")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    approve_response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/approve",
        json={},
        headers=auth_headers,
    )
    reject_response = client.patch(
        f"/api/v1/admin/verification-requests/{request_id}/reject",
        json={"rejection_reason": "not allowed"},
        headers=auth_headers,
    )

    assert approve_response.status_code == 403
    assert reject_response.status_code == 403


def test_general_user_cannot_access_admin_api(client, auth_headers, created_target):
    """일반 사용자가 관리자 API 접근 실패"""
    response = client.get(
        "/api/v1/admin/verification-requests",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_invalid_status_rejected(client, admin_headers):
    """잘못된 status 요청은 실패해야 한다."""
    response = client.get(
        "/api/v1/admin/verification-requests?status=INVALID",
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_duplicate_pending_request_rejected(client, auth_headers, created_target):
    """이미 미결정 요청이 있으면 새 요청 거절"""
    # 첫 번째 요청 생성
    response1 = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "family_relation_certificate"},
        files={"file": ("cert1.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert response1.status_code == 201

    # 두 번째 요청 시도 - 실패해야 함
    response2 = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "id_card"},
        files={"file": ("cert2.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert response2.status_code == 400


def test_invalid_file_type_rejected(client, auth_headers, created_target):
    """지원하지 않는 파일 형식 거절"""
    response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "family_relation_certificate"},
        files={"file": ("audio.mp3", b"fake audio content", "audio/mpeg")},
        headers=auth_headers,
    )
    assert response.status_code == 400

