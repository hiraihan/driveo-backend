from dataclasses import dataclass
from datetime import date
from math import floor, ceil
from typing import Protocol, Optional

class PromoProtocol(Protocol):
    discount_percent: float
    max_discount_amount: int

@dataclass(frozen=True)
class Quote:
    hari: int
    harga_per_hari: int
    subtotal: int
    diskon: int
    total_nilai: int
    dp: int
    sisa: int

def quote(harga_per_hari: int, tanggal_mulai: date, tanggal_selesai: date, promo: Optional[PromoProtocol], dp_percent: float) -> Quote:
    hari = (tanggal_selesai - tanggal_mulai).days + 1
    subtotal = harga_per_hari * hari
    diskon = 0
    if promo:
        diskon = min(floor(subtotal * promo.discount_percent / 100), promo.max_discount_amount)
    
    total = subtotal - diskon
    dp = ceil(total * dp_percent / 100)
    sisa = total - dp
    
    return Quote(
        hari=hari,
        harga_per_hari=harga_per_hari,
        subtotal=subtotal,
        diskon=diskon,
        total_nilai=total,
        dp=dp,
        sisa=sisa
    )
