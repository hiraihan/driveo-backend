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
