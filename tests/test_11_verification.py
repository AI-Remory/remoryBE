"""Target Verification Tests"""
import pytest


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
    assert data["verification_type"] == "family_relation_certificate"
    assert data["status"] == "pending"
    assert data["original_filename"] == "cert.pdf"
    assert data["mime_type"] == "application/pdf"


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
    assert data["items"][0]["status"] == "pending"


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
    assert data["status"] == "pending"


def test_list_pending_requests_admin(client, auth_headers, admin_headers, created_target):
    """미검토 요청 목록 조회 (관리자)"""
    # 일반 사용자가 요청 생성
    create_response = client.post(
        f"/api/v1/targets/{created_target['id']}/verification-requests",
        data={"verification_type_param": "family_relation_certificate"},
        files={"file": ("cert.pdf", b"fake pdf content", "application/pdf")},
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    # 관리자가 목록 조회
    response = client.get(
        "/api/v1/admin/verification-requests",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


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
    assert data["status"] == "approved"
    assert data["reviewed_by"] is not None
    assert data["reviewed_at"] is not None


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
    assert data["status"] == "rejected"
    assert data["reviewed_by"] is not None
    assert data["rejection_reason"] == "Document is not clear and needs higher quality image"


def test_general_user_cannot_access_admin_api(client, auth_headers, created_target):
    """일반 사용자가 관리자 API 접근 실패"""
    response = client.get(
        "/api/v1/admin/verification-requests",
        headers=auth_headers,
    )
    assert response.status_code == 403


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

