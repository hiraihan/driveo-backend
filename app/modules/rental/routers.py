from sqlalchemy.future import select
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.rental.models import Rental, RentalPayoutAccount, RentalStaff
from app.modules.auth.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

class OnboardRequest(BaseModel):
    nama_usaha: str
    nib: str
    alamat: str
    kontak: str
    payout_account: str

@router.post("/onboard", status_code=201)
async def onboard_rental(req: OnboardRequest, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Mock encryption for payout account
    encrypted_payout = f"ENCRYPTED_{req.payout_account}"
    
    rental = Rental(nama_usaha=req.nama_usaha, nib=req.nib, alamat=req.alamat, kontak=req.kontak)
    db.add(rental)
    await db.flush()
    
    payout = RentalPayoutAccount(rental_id=rental.id, encrypted_account_info=encrypted_payout)
    staff = RentalStaff(rental_id=rental.id, user_id=current_user["sub"], role="Admin")
    
    db.add(payout)
    db.add(staff)
    await db.commit()
    
    return {"id": rental.id, "nama_usaha": rental.nama_usaha, "status": rental.status_verifikasi}
from app.modules.rental.models import RentalVerification
from app.mocks.ports import MockAuditPort

class VerifyRequest(BaseModel):
    status: str
    alasan: str

@router.post("/{rental_id}/verify")
async def verify_rental(rental_id: str, req: VerifyRequest, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.get("role") != "Admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    result = await db.execute(select(Rental).where(Rental.id == rental_id))
    rental = result.scalars().first()
    if not rental:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Rental not found")
        
    rental.status_verifikasi = req.status
    verif = RentalVerification(rental_id=rental.id, hasil=req.status, alasan=req.alasan, reviewer_id=current_user["sub"])
    db.add(verif)
    await db.commit()
    
    audit_port = MockAuditPort()
    audit_port.log_event("RENTAL_VERIFIED", {"rental_id": rental.id, "status": req.status, "reviewer": current_user["sub"]})
    
    return {"message": "Verification recorded"}
