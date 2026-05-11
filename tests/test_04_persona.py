def test_create_and_get_persona(client, auth_headers, created_persona):
    response = client.get(f"/api/v1/personas/{created_persona['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_persona["id"]
    assert response.json()["status"] == "READY"
    assert response.json()["persona_name"]


def test_persona_status(client, auth_headers, created_persona):
    response = client.get(f"/api/v1/personas/{created_persona['id']}/status", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "READY"


def test_create_persona_requires_verification(client, auth_headers, created_target, uploaded_media, target_persona_consent):
    """Test that persona creation fails without target verification."""
    target_id = created_target["id"]
    response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)
    assert response.status_code == 403
    assert "Target verification approval is required" in response.json()["detail"]


def test_create_persona_with_verification(client, auth_headers, created_target, uploaded_media, target_persona_consent):
    """Test that persona creation succeeds with target verification."""
    from app.models.target_verification import TargetVerificationRequest, VerificationStatus, VerificationType
    from datetime import datetime, UTC
    from sqlalchemy.orm import sessionmaker
    from app.core.database import engine

    # Create a test session to add verification
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    try:
        # Get current user ID from token
        user_response = client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = user_response.json()["id"]

        target_id = created_target["id"]

        # Create approved verification
        verification = TargetVerificationRequest(
            user_id=user_id,
            target_id=target_id,
            verification_type=VerificationType.SELF_DECLARATION,
            status=VerificationStatus.APPROVED,
            document_file_path="test/verification.pdf",
            original_filename="verification.pdf",
            stored_filename="test_verification.pdf",
            mime_type="application/pdf",
            file_size=1024,
            submitted_at=datetime.now(UTC).replace(tzinfo=None),
            reviewed_at=datetime.now(UTC).replace(tzinfo=None),
            reviewed_by=user_id,
        )
        db.add(verification)
        db.commit()

        # Now persona creation should succeed
        response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["status"] == "READY"
    finally:
        db.close()


def test_create_persona_requires_consent(client, auth_headers, uploaded_media):
    target_id = uploaded_media["image"]["target_id"]
    response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)
    assert response.status_code == 403


def test_other_user_cannot_access_persona(client, created_persona, second_user_headers):
    response = client.get(f"/api/v1/personas/{created_persona['id']}", headers=second_user_headers)
    assert response.status_code in (403, 404)


