from datetime import date

def calculate_refund_amount(total_nilai: float, dp: float, tanggal_mulai: date, tanggal_batal: date) -> float:
    delta_days = (tanggal_mulai - tanggal_batal).days
    
    if delta_days >= 2:
        return total_nilai # 100% (or DP depending on BR, SRS usually says H-2 = full)
    elif delta_days == 1:
        return total_nilai * 0.5 # 50%
    else:
        return 0 # No refund for D-day or later
