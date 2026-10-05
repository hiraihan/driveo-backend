import pytest
from app.modules.verification.service import VerificationService
from app.core.config import get_settings
from app.core.enums import VerificationStatus
from tests.factories import make_user, auth_header, make_admin
import io

@pytest.mark.asyncio
async def test_filename_ignored(client, db, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    u = await make_user(db)
    
    ktp_file = io.BytesIO(b"fake image data")
    selfie_file = io.BytesIO(b"fake image data")
    
    files = {
        "ktp": ("../../evil.png", ktp_file, "image/png"),
        "selfie": ("valid.jpg", selfie_file, "image/jpeg")
    }
    
    res = await client.post("/verifications", files=files, headers=auth_header(u))
    assert res.status_code == 201
    
    # Check if files were saved inside tmp_path/verifications and not traversed
    import os
    saved_files = os.listdir(tmp_path / "verifications")
    assert len(saved_files) == 2
    for f in saved_files:
        assert "../../" not in f
        assert "evil.png" not in f
        assert f.endswith(".png") or f.endswith(".jpg")

@pytest.mark.asyncio
async def test_rejects_pdf(client, db):
    u = await make_user(db)
    files = {
        "ktp": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf"),
        "selfie": ("valid.jpg", io.BytesIO(b"fake image"), "image/jpeg")
    }
    res = await client.post("/verifications", files=files, headers=auth_header(u))
    assert res.status_code == 415

@pytest.mark.asyncio
async def test_rejects_large(client, db, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 10)
    u = await make_user(db)
    files = {
        "ktp": ("test.png", io.BytesIO(b"large string 12345"), "image/png"),
        "selfie": ("valid.jpg", io.BytesIO(b"large string 12345"), "image/jpeg")
    }
    res = await client.post("/verifications", files=files, headers=auth_header(u))
    assert res.status_code == 413

@pytest.mark.asyncio
async def test_second_submission_409(client, db, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    u = await make_user(db)
    
    def get_files():
        return {
            "ktp": ("test.png", io.BytesIO(b"fake"), "image/png"),
            "selfie": ("valid.jpg", io.BytesIO(b"fake"), "image/jpeg")
        }
    
    res1 = await client.post("/verifications", files=get_files(), headers=auth_header(u))
    assert res1.status_code == 201
    
    res2 = await client.post("/verifications", files=get_files(), headers=auth_header(u))
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "VERIFICATION_EXISTS"

@pytest.mark.asyncio
async def test_admin_review_sets_status(client, db, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    u = await make_user(db)
    admin = await make_admin(db)
    
    files = {
        "ktp": ("test.png", io.BytesIO(b"fake"), "image/png"),
        "selfie": ("valid.jpg", io.BytesIO(b"fake"), "image/jpeg")
    }
    res = await client.post("/verifications", files=files, headers=auth_header(u))
    v_id = res.json()["id"]
    
    review_res = await client.post(f"/verifications/{v_id}/review", json={"status": "TERVERIFIKASI", "alasan": None}, headers=auth_header(admin))
    assert review_res.status_code == 200
    
    svc = VerificationService(db)
    status = await svc.get_status(u.id)
    assert status == VerificationStatus.TERVERIFIKASI

@pytest.mark.asyncio
async def test_response_has_no_ocr(client, db, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    u = await make_user(db)
    
    files = {
        "ktp": ("test.png", io.BytesIO(b"fake"), "image/png"),
        "selfie": ("valid.jpg", io.BytesIO(b"fake"), "image/jpeg")
    }
    res = await client.post("/verifications", files=files, headers=auth_header(u))
    assert "ocr_result" not in res.json()
