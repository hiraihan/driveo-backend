from pydantic import Field
from app.core.schemas import RequestModel, ResponseModel
from app.core.enums import PaymentType, PaymentStatus

class PaymentIntentRequest(RequestModel):
    type: PaymentType

class PaymentIntentResponse(ResponseModel):
    order_id: str
    amount: int
    type: PaymentType
    status: PaymentStatus
    redirect_url: str

class MidtransNotification(RequestModel):
    order_id: str
    status_code: str
    gross_amount: str
    signature_key: str
    transaction_status: str
    transaction_id: str
