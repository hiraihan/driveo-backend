import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings
from app.modules.user.models import User
from app.modules.user.service import get_or_create_role
from app.core.enums import UserRole
from app.modules.auth.security import hash_password
from app.core.ids import new_id
from app.modules.marketplace import models as m


def _iso(**kwargs) -> str:
    return datetime.now(timezone.utc) - timedelta(**kwargs)


PICKUP_SPOTS = [
    {"id": "spot-yia", "name": "Bandara Internasional Yogyakarta (YIA)", "code": "YIA",
     "area": "Kulon Progo", "description": "Zona Penjemputan Terminal Kedatangan / Drop-off Area",
     "extra_fee": 100000, "is_popular": True, "estimated_delivery_min": 45},
    {"id": "spot-tugu", "name": "Stasiun Tugu Yogyakarta", "code": "YK-TUGU",
     "area": "Kota Yogyakarta (Pusat)", "description": "Pintu Selatan (Jl. Pasar Kembang) & Pintu Barat Bong Suwung",
     "extra_fee": 0, "is_popular": True, "estimated_delivery_min": 15},
    {"id": "spot-lempuyangan", "name": "Stasiun Lempuyangan", "code": "YK-LPN",
     "area": "Danurejan, Kota Yogyakarta", "description": "Drop-off Zone Pintu Timur Jl. Lempuyangan",
     "extra_fee": 0, "is_popular": True, "estimated_delivery_min": 20},
    {"id": "spot-malioboro", "name": "Kawasan Malioboro & Sosrowijayan", "code": "YK-MLBR",
     "area": "Gedongtengen, Kota Yogyakarta", "description": "Lobi Hotel / Titik Temu Area Malioboro",
     "extra_fee": 0, "is_popular": True, "estimated_delivery_min": 15},
    {"id": "spot-sleman", "name": "Garasi Mitra Sleman (Jl. Magelang)", "code": "SLM-MLT",
     "area": "Mlati, Sleman", "description": "Jl. Magelang Km 7.5, Mlati, Sleman",
     "extra_fee": 0, "is_popular": False, "estimated_delivery_min": 0},
    {"id": "spot-bantul", "name": "Garasi Mitra Bantul (Jl. Bantul)", "code": "BTL-SWN",
     "area": "Sewon, Bantul", "description": "Jl. Bantul Km 5.5, Sewon, Bantul",
     "extra_fee": 0, "is_popular": False, "estimated_delivery_min": 0},
]

RENTALS = [
    {
        "id": "rental-tugu", "name": "Tugu Rent Jogja", "slug": "tugu-rent-jogja",
        "nib": "0220108921844", "nib_verified": True, "rating": 4.97, "total_reviews": 142,
        "completed_bookings": 642, "address": "Jl. Sosrowijayan No. 42, Sosromenduran, Gedongtengen",
        "district": "Gedongtengen", "city": "Kota Yogyakarta", "phone": "+62 274 589 123",
        "whatsapp": "+62 812 3456 7890", "operating_hours": "06:00 - 23:00 WIB (Antar-Jemput 24 Jam)",
        "description": "Mitra rental resmi berizin OSS-RBA dengan pengalaman 8 tahun di pusat kota Yogyakarta. Mengkhususkan armada MPV & mobil keluarga dengan perawatan berkala bengkel resmi Toyota. Titik garasi hanya 3 menit dari Stasiun Tugu Yogyakarta.",
        "avatar_url": "https://images.unsplash.com/photo-1560179707-f14e90ef3623?auto=format&fit=crop&w=300&q=80",
        "banner_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
        "established_year": 2017,
        "coverage_spot_ids": ["spot-tugu", "spot-yia", "spot-lempuyangan", "spot-malioboro"],
        "features": ["Izin Usaha NIB OSS-RBA Terverifikasi", "Garansi Unit Bersih & Steril",
                     "Layanan Antar-Jemput Stasiun Tugu & YIA", "Asuransi All Risk Komprehensif", "Dukungan Darurat 24 Jam"],
        "reviews": [
            {"id": "rev-01", "authorName": "Dimas Anggara", "authorCity": "Jakarta Selatan", "rating": 5,
             "date": "28 September 2026",
             "comment": "Zenix Hybrid sangat terawat! Mobil diantar tepat waktu di Stasiun Tugu pintu barat. AC sejuk, bau mobil baru, serah terima via digital checklist cepat sekali.",
             "vehicleName": "Toyota Innova Zenix 2.0 Q Hybrid TSS 2024",
             "merchantReply": {"author": "Bambang Sudibyo (Owner Tugu Rent)", "date": "28 September 2026",
                               "comment": "Matur nuwun Mas Dimas atas kepercayaannya! Senang sekali Zenix kami bisa menemani perjalanan keluarga di Jogja. Sampai jumpa di liburan berikutnya!"}},
            {"id": "rev-02", "authorName": "Sarah Wijaya", "authorCity": "Surabaya", "rating": 5,
             "date": "15 September 2026",
             "comment": "Sangat puas sewa Avanza di sini. Lepas kunci mudah dan verifikasi e-KYC DriveO langsung beres. CS ramah dan solutif waktu tanya rekomendasi rute ke Mangunan.",
             "vehicleName": "Toyota All New Avanza 1.5 G CVT TSS 2023"},
        ],
    },
    {
        "id": "rental-sleman", "name": "Sleman Auto Perkasa", "slug": "sleman-auto-perkasa",
        "nib": "9120204719283", "nib_verified": True, "rating": 4.93, "total_reviews": 98,
        "completed_bookings": 388, "address": "Jl. Magelang Km 7.5, Sendangadi, Mlati",
        "district": "Mlati", "city": "Sleman", "phone": "+62 274 864 771",
        "whatsapp": "+62 813 9876 5432", "operating_hours": "07:00 - 22:00 WIB",
        "description": "Spesialis armada SUV tangguh dan MPV premium di Sleman Utara. Sangat cocok bagi wisatawan yang ingin menjelajah lereng Merapi, Kaliurang, maupun rute perbukitan Menoreh Kulon Progo.",
        "avatar_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=300&q=80",
        "banner_url": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80",
        "established_year": 2019,
        "coverage_spot_ids": ["spot-sleman", "spot-yia", "spot-tugu"],
        "features": ["Spesialis SUV Ground Clearance Tinggi", "Kondisi Ban & Rem Selalu Standar OEM",
                     "Bebas Biaya Jemput Garasi Sleman", "Free Car Seat Anak (Request Dahulu)"],
        "reviews": [
            {"id": "rev-03", "authorName": "Rian Hidayat", "authorCity": "Bandung", "rating": 5,
             "date": "20 September 2026",
             "comment": "Xforce-nya jos gandos! Tanjakan Kaliurang libas enteng. Ground clearance tinggi bikin tenang lewat jalan berlubang. Unit sangat bersih.",
             "vehicleName": "Mitsubishi Xforce Ultimate 1.5 CVT 2024",
             "merchantReply": {"author": "Agus Pratama (Sleman Auto)", "date": "21 September 2026",
                               "comment": "Terima kasih Mas Rian! Xforce memang jagoan kami untuk rute perbukitan Jogja. Ditunggu kunjungan berikutnya nggih!"}},
        ],
    },
    {
        "id": "rental-malioboro", "name": "Malioboro Trans Mobility", "slug": "malioboro-trans-mobility",
        "nib": "1203000918231", "nib_verified": True, "rating": 4.95, "total_reviews": 112,
        "completed_bookings": 472, "address": "Jl. Dagen No. 18, Sosromenduran, Gedongtengen",
        "district": "Gedongtengen", "city": "Kota Yogyakarta", "phone": "+62 274 512 889",
        "whatsapp": "+62 811 2345 678", "operating_hours": "24 Jam Non-Stop",
        "description": "Pelopor armada ramah lingkungan Kendaraan Listrik (EV) dan City Car modern di jantung pariwisata Malioboro. Siap antar-jemput ke seluruh hotel bintang dan penginapan di DIY.",
        "avatar_url": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?auto=format&fit=crop&w=300&q=80",
        "banner_url": "https://images.unsplash.com/photo-1508974239320-0a029497e820?auto=format&fit=crop&w=1200&q=80",
        "established_year": 2021,
        "coverage_spot_ids": ["spot-malioboro", "spot-tugu", "spot-yia"],
        "features": ["Armada EV Ioniq 5 Baterai Penuh 100%", "Edukasi Pengisian SPKLU Jogja",
                     "Layanan Antar Hotel Malioboro Gratis", "Fast Response 24 Jam via WhatsApp"],
        "reviews": [
            {"id": "rev-04", "authorName": "Jessica Tan", "authorCity": "Tangerang", "rating": 5,
             "date": "12 September 2026",
             "comment": "Nyobain Ioniq 5 keliling Jogja seru banget! Senyap, AC dingin, gak pusing antre bensin. Rental jelasin cara charge dengan sangat detail.",
             "vehicleName": "Hyundai Ioniq 5 Signature Long Range 2024"},
        ],
    },
    {
        "id": "rental-kencana", "name": "Kencana Rent Jogja Selatan", "slug": "kencana-rent-jogja-selatan",
        "nib": "8120005189210", "nib_verified": True, "rating": 4.89, "total_reviews": 64,
        "completed_bookings": 295, "address": "Jl. Bantul Km 5.5, Pendowoharjo, Sewon",
        "district": "Sewon", "city": "Bantul", "phone": "+62 274 646 220",
        "whatsapp": "+62 815 6789 0123", "operating_hours": "07:00 - 21:00 WIB",
        "description": "Pilihan terpercaya untuk rental mobil hemat, City Car lincah, dan armada terawat untuk area Bantul, Kasongan, Parangtritis, dan Kota Jogja.",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80",
        "banner_url": "https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?auto=format&fit=crop&w=1200&q=80",
        "established_year": 2020,
        "coverage_spot_ids": ["spot-bantul", "spot-tugu", "spot-lempuyangan"],
        "features": ["Harga Ramah Wisatawan & Mahasiswa", "Brio RS Kondisi Prima & Irit", "Bebas Biaya Antar Area Sewon & Bantul"],
        "reviews": [
            {"id": "rev-05", "authorName": "Anindya Putri", "authorCity": "Semarang", "rating": 5,
             "date": "5 September 2026",
             "comment": "Brio-nya super lincah masuk gang-gang sentra keramik Kasongan. Pelayanan gercep dan proses deposit lancar!",
             "vehicleName": "Honda Brio RS Urbanite Edition CVT 2023"},
        ],
    },
]

VEHICLES = [
    {
        "id": "veh-zenix-01", "rental_id": "rental-tugu", "rental_name": "Tugu Rent Jogja",
        "rental_rating": 4.97, "rental_completed_bookings": 642,
        "name": "Toyota Innova Zenix 2.0 Q Hybrid TSS 2024", "brand": "Toyota", "model": "Innova Zenix Hybrid",
        "year": 2024, "license_plate": "AB 1001 QZ", "category": "MPV", "transmission": "CVT",
        "fuel_type": "HYBRID", "seating_capacity": 7, "luggage_capacity": 4, "engine_capacity_cc": 1987,
        "features": ["Toyota Safety Sense 3.0", "Panoramic Sunroof", "Captain Seat Ottoman Elektrik",
                     "Wireless Apple CarPlay & Android Auto", "Kamera 360 Derajat"],
        "thumbnail_url": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=1200&q=80"],
        "status": "TERSEDIA", "base_daily_rate": 650000, "security_deposit": 250000, "delivery_fee": 0,
        "city": "Kota Yogyakarta", "district": "Gedongtengen",
        "garage_address": "Jl. Sosrowijayan No. 42 (Dekat Stasiun Tugu)",
        "last_updated_at": _iso(minutes=15), "is_popular": True,
    },
    {
        "id": "veh-xforce-01", "rental_id": "rental-sleman", "rental_name": "Sleman Auto Perkasa",
        "rental_rating": 4.93, "rental_completed_bookings": 388,
        "name": "Mitsubishi Xforce Ultimate 1.5 CVT 2024", "brand": "Mitsubishi", "model": "Xforce Ultimate",
        "year": 2024, "license_plate": "AB 1890 DX", "category": "SUV", "transmission": "CVT",
        "fuel_type": "BENSIN", "seating_capacity": 5, "luggage_capacity": 3, "engine_capacity_cc": 1499,
        "features": ["Yamaha Dynamic Sound Premium", "Drive Mode: Wet / Gravel / Mud / Normal",
                     "Dual Zone AC Nanoe-X", "Blind Spot Warning & RCTA", "Ground Clearance 222 mm (Siap Merapi)"],
        "thumbnail_url": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": ["https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80"],
        "status": "TERSEDIA", "base_daily_rate": 550000, "security_deposit": 200000, "delivery_fee": 0,
        "city": "Sleman", "district": "Mlati", "garage_address": "Jl. Magelang Km 7.5, Mlati",
        "last_updated_at": _iso(minutes=25), "is_popular": True,
    },
    {
        "id": "veh-ioniq-01", "rental_id": "rental-malioboro", "rental_name": "Malioboro Trans Mobility",
        "rental_rating": 4.95, "rental_completed_bookings": 472,
        "name": "Hyundai Ioniq 5 Signature Long Range 2024", "brand": "Hyundai", "model": "Ioniq 5 Long Range",
        "year": 2024, "license_plate": "AB 1555 EV", "category": "EV", "transmission": "AUTOMATIC",
        "fuel_type": "LISTRIK", "seating_capacity": 5, "luggage_capacity": 4, "engine_capacity_cc": 0,
        "features": ["Jarak Tempuh 451 KM Sekali Charge", "V2L (Vehicle to Load) Colokan 220V",
                     "Hyundai SmartSense ADAS", "Vision Roof & Relax Comfort Seat", "Gratis Akses SPKLU Tertentu di Jogja"],
        "thumbnail_url": "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": ["https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=1200&q=80"],
        "status": "TERSEDIA", "base_daily_rate": 850000, "security_deposit": 350000, "delivery_fee": 50000,
        "city": "Kota Yogyakarta", "district": "Gedongtengen", "garage_address": "Jl. Dagen No. 18, Malioboro",
        "last_updated_at": _iso(minutes=40), "is_popular": True,
    },
    {
        "id": "veh-avanza-01", "rental_id": "rental-tugu", "rental_name": "Tugu Rent Jogja",
        "rental_rating": 4.97, "rental_completed_bookings": 642,
        "name": "Toyota All New Avanza 1.5 G CVT TSS 2023", "brand": "Toyota", "model": "All New Avanza",
        "year": 2023, "license_plate": "AB 1234 XY", "category": "MPV", "transmission": "CVT",
        "fuel_type": "BENSIN", "seating_capacity": 7, "luggage_capacity": 3, "engine_capacity_cc": 1496,
        "features": ["Sofa Mode Interior Nyaman", "Toyota Safety Sense (TSS)", "Rear Parking Camera & Sensor",
                     "Irit BBM Konsumsi 1:16 KM/L", "AC Double Blower Dingin Merata"],
        "thumbnail_url": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": ["https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1200&q=80"],
        "status": "TERSEDIA", "base_daily_rate": 400000, "security_deposit": 150000, "delivery_fee": 0,
        "city": "Kota Yogyakarta", "district": "Gedongtengen", "garage_address": "Jl. Sosrowijayan No. 42",
        "last_updated_at": _iso(minutes=50), "is_popular": True,
    },
    {
        "id": "veh-brio-01", "rental_id": "rental-kencana", "rental_name": "Kencana Rent Jogja Selatan",
        "rental_rating": 4.89, "rental_completed_bookings": 295,
        "name": "Honda Brio RS Urbanite Edition CVT 2023", "brand": "Honda", "model": "Brio RS Urbanite",
        "year": 2023, "license_plate": "AB 1420 JK", "category": "CITY_CAR", "transmission": "CVT",
        "fuel_type": "BENSIN", "seating_capacity": 5, "luggage_capacity": 2, "engine_capacity_cc": 1199,
        "features": ["Lincah Parkir di Gang Kota & Malioboro", "Audio Display Touchscreen",
                     "Konsumsi BBM Sangat Irit (1:18 KM/L)", "Dual SRS Airbags & ABS EBD", "AC Digital Dingin Cepat"],
        "thumbnail_url": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": ["https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80"],
        "status": "TERSEDIA", "base_daily_rate": 350000, "security_deposit": 150000, "delivery_fee": 0,
        "city": "Bantul", "district": "Sewon", "garage_address": "Jl. Bantul Km 5.5, Sewon",
        "last_updated_at": _iso(minutes=90), "is_popular": False,
    },
    {
        "id": "veh-fortuner-01", "rental_id": "rental-sleman", "rental_name": "Sleman Auto Perkasa",
        "rental_rating": 4.93, "rental_completed_bookings": 388,
        "name": "Toyota Fortuner 2.8 VRZ GR Sport 4x2 2024", "brand": "Toyota", "model": "Fortuner 2.8 GR Sport",
        "year": 2024, "license_plate": "AB 1999 FZ", "category": "SUV", "transmission": "AUTOMATIC",
        "fuel_type": "DIESEL", "seating_capacity": 7, "luggage_capacity": 4, "engine_capacity_cc": 2755,
        "features": ["Mesin 1GD-FTV 204 PS Torsi 500 Nm", "Power Backdoor dengan Kick Sensor",
                     "Suspensi GR Sport Nyaman di Tanjakan", "Wireless Charger & Rear Seat Entertainment", "Kamera 360 Panoramic View Monitor"],
        "thumbnail_url": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": ["https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=80"],
        "status": "TERSEDIA", "base_daily_rate": 1100000, "security_deposit": 500000, "delivery_fee": 0,
        "city": "Sleman", "district": "Mlati", "garage_address": "Jl. Magelang Km 7.5",
        "last_updated_at": _iso(minutes=30), "is_popular": False,
    },
]

# Extra mitra fleet vehicles (for `/mitra/kendaraan` pages, owned by rental-tugu)
MITRA_VEHICLES = [
    {
        "id": "veh-tugu-01", "rental_id": "rental-tugu", "rental_name": "Tugu Rent Jogja",
        "rental_rating": 4.97, "rental_completed_bookings": 642,
        "name": "Toyota Innova Zenix 2.0 Q Hybrid TSS 2024", "brand": "Toyota", "model": "Innova Zenix Hybrid",
        "year": 2024, "license_plate": "AB 1001 QZ", "category": "MPV", "transmission": "CVT",
        "fuel_type": "HYBRID", "seating_capacity": 7, "luggage_capacity": 4, "engine_capacity_cc": 1987,
        "features": ["Toyota Safety Sense 3.0", "Panoramic Sunroof", "Captain Seat Ottoman Elektrik",
                     "Wireless Apple CarPlay & Android Auto", "Kamera 360 Derajat"],
        "thumbnail_url": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1200&q=80"],
        "status": "TERSEDIA", "base_daily_rate": 650000, "security_deposit": 250000, "delivery_fee": 0,
        "city": "Kota Yogyakarta", "district": "Gedongtengen",
        "garage_address": "Jl. Sosrowijayan No. 42 (Dekat Stasiun Tugu)",
        "last_updated_at": _iso(days=2), "is_popular": True,
        "stnk_number": "STNK-DIY-2024-88491", "stnk_tax_expiry_date": "2027-04-18",
        "stnk_photo_url": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800&q=80",
        "odometer_km": 18450, "next_service_km": 20000, "next_service_date": "2026-11-15",
        "equipment_checklist": {"hasSpareTire": True, "hasJack": True, "hasWarningTriangle": True,
                                "hasFirstAidKit": True, "hasToolKit": True, "hasFireExtinguisher": True},
        "service_history": [{"id": "srv-01", "date": "2026-08-10", "workshopName": "Nasmoco Toyota Janti Yogyakarta",
                             "odometerKm": 15120, "description": "Servis berkala 15.000 KM, ganti oli mesin 0W-20 TMO, rotasi ban, cek sistem TSS",
                             "cost": 1450000}],
    },
    {
        "id": "veh-tugu-02", "rental_id": "rental-tugu", "rental_name": "Tugu Rent Jogja",
        "rental_rating": 4.97, "rental_completed_bookings": 642,
        "name": "Toyota All New Avanza 1.5 G CVT TSS 2023", "brand": "Toyota", "model": "All New Avanza",
        "year": 2023, "license_plate": "AB 1234 XY", "category": "MPV", "transmission": "CVT",
        "fuel_type": "BENSIN", "seating_capacity": 7, "luggage_capacity": 3, "engine_capacity_cc": 1496,
        "features": ["Sofa Mode Interior Nyaman", "Toyota Safety Sense (TSS)", "Rear Parking Camera & Sensor",
                     "Irit BBM Konsumsi 1:16 KM/L", "AC Double Blower Dingin Merata"],
        "thumbnail_url": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80"],
        "status": "DALAM_SEWA", "base_daily_rate": 400000, "security_deposit": 150000, "delivery_fee": 0,
        "city": "Kota Yogyakarta", "district": "Gedongtengen", "garage_address": "Jl. Sosrowijayan No. 42",
        "last_updated_at": _iso(days=1), "is_popular": True,
        "stnk_number": "STNK-DIY-2023-11029", "stnk_tax_expiry_date": "2026-10-25",
        "stnk_photo_url": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800&q=80",
        "odometer_km": 42100, "next_service_km": 45000, "next_service_date": "2026-11-30",
        "equipment_checklist": {"hasSpareTire": True, "hasJack": True, "hasWarningTriangle": True,
                                "hasFirstAidKit": True, "hasToolKit": True, "hasFireExtinguisher": True},
        "service_history": [{"id": "srv-02", "date": "2026-07-02", "workshopName": "Nasmoco Mlati Sleman",
                             "odometerKm": 39800, "description": "Servis berkala 40.000 KM, tune up mesin, ganti filter AC & kampas rem depan",
                             "cost": 2100000}],
    },
    {
        "id": "veh-tugu-03", "rental_id": "rental-tugu", "rental_name": "Tugu Rent Jogja",
        "rental_rating": 4.97, "rental_completed_bookings": 642,
        "name": "Mitsubishi Xpander Ultimate CVT 2024", "brand": "Mitsubishi", "model": "Xpander Ultimate",
        "year": 2024, "license_plate": "AB 1782 FA", "category": "MPV", "transmission": "CVT",
        "fuel_type": "BENSIN", "seating_capacity": 7, "luggage_capacity": 3, "engine_capacity_cc": 1499,
        "features": ["Ground Clearance 220mm", "Electric Parking Brake & Auto Hold", "Wireless Charger",
                     "Suspensi Halus Senyaman Sedan", "Cruise Control"],
        "thumbnail_url": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": [
            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80"],
        "status": "SERVIS_RUTIN", "base_daily_rate": 450000, "security_deposit": 200000, "delivery_fee": 0,
        "city": "Kota Yogyakarta", "district": "Gedongtengen", "garage_address": "Jl. Sosrowijayan No. 42",
        "last_updated_at": _iso(days=4), "is_popular": False,
        "stnk_number": "STNK-DIY-2024-34901", "stnk_tax_expiry_date": "2027-02-14",
        "stnk_photo_url": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800&q=80",
        "odometer_km": 28900, "next_service_km": 30000, "next_service_date": "2026-10-08",
        "equipment_checklist": {"hasSpareTire": True, "hasJack": True, "hasWarningTriangle": True,
                                "hasFirstAidKit": True, "hasToolKit": True, "hasFireExtinguisher": False},
        "service_history": [{"id": "srv-03", "date": "2026-05-18", "workshopName": "Mitsubishi Borobudur Motors Magelang",
                             "odometerKm": 20100, "description": "Penggantian kampas rem belakang dan kuras minyak rem",
                             "cost": 1650000}],
    },
    {
        "id": "veh-tugu-04", "rental_id": "rental-tugu", "rental_name": "Tugu Rent Jogja",
        "rental_rating": 4.97, "rental_completed_bookings": 642,
        "name": "Honda Brio RS CVT 2023", "brand": "Honda", "model": "Brio RS",
        "year": 2023, "license_plate": "AB 1899 TK", "category": "CITY_CAR", "transmission": "CVT",
        "fuel_type": "BENSIN", "seating_capacity": 5, "luggage_capacity": 2, "engine_capacity_cc": 1199,
        "features": ["Irit BBM Kota Jogja", "Lincah Parkir di Kawasan Padat", "Audio Touchscreen Bluetooth", "Sporty Alloy Wheels"],
        "thumbnail_url": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80",
        "gallery_images": ["https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80"],
        "status": "TERSEDIA", "base_daily_rate": 350000, "security_deposit": 150000, "delivery_fee": 0,
        "city": "Kota Yogyakarta", "district": "Gedongtengen", "garage_address": "Jl. Sosrowijayan No. 42",
        "last_updated_at": _iso(days=3), "is_popular": False,
        "stnk_number": "STNK-DIY-2023-77182", "stnk_tax_expiry_date": "2027-08-20",
        "odometer_km": 34100, "next_service_km": 40000, "next_service_date": "2027-01-10",
        "equipment_checklist": {"hasSpareTire": True, "hasJack": True, "hasWarningTriangle": True,
                                "hasFirstAidKit": True, "hasToolKit": True, "hasFireExtinguisher": True},
    },
]

DISPUTES = [
    {
        "id": "dsp-demo-01", "ticket_code": "DSP-202610-0089", "booking_id": "bk-active-demo-03",
        "booking_code": "DVO-202610-7731", "vehicle_name": "Honda Brio RS CVT Facelift 2024",
        "vehicle_thumbnail": "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=800&q=80",
        "rental_name": "Tugu Rent Jogja", "category": "KLAIM_DEPOSIT_SEPIHAK",
        "description": "Pihak mitra rental mengklaim potongan deposit sebesar Rp 150.000 atas baret halus di bemper kanan depan. Namun pada foto checklist serah terima awal, baret halus tersebut sudah ada sebelum serah terima kunci dilakukan.",
        "claimed_amount": 150000,
        "demands": "Pencairan deposit jaminan 100% penuh kembali ke rekening penyewa tanpa potongan sepihak.",
        "renter_evidence_urls": [
            "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=800&q=80"],
        "partner_evidence_urls": ["https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=800&q=80"],
        "status": "INVESTIGASI_BUKTI", "created_at": "2026-10-04T14:30:00+07:00",
        "timeline": [
            {"id": "evt-1", "timestamp": "2026-10-04T14:30:00+07:00", "actor": "PENYEWA",
             "title": "Tiket Sengketa Resmi Dibuka",
             "description": "Penyewa mengajukan keberatan resmi atas klaim pemotongan deposit sepihak oleh Tugu Rent Jogja."},
            {"id": "evt-2", "timestamp": "2026-10-04T15:10:00+07:00", "actor": "MEDIATOR_DRIVEO",
             "title": "Kasus Diterima Tim Mediasi Independen",
             "description": "Tim Mediasi DriveO membekukan pelepasan dana deposit di rekening penampung escrow dan meminta data digital inspeksi serah terima."},
            {"id": "evt-3", "timestamp": "2026-10-04T17:00:00+07:00", "actor": "MITRA",
             "title": "Mitra Menyerahkan Foto Pembanding",
             "description": "Mitra Tugu Rent mengunggah foto jarak dekat baret pada bemper dan estimasi biaya kompon poles salon mobil sebesar Rp 75.000."},
        ],
        "mediator_verdict": {
            "decidedAt": "2026-10-05T09:00:00+07:00",
            "mediatorName": "Rian Hendrawan, S.H. (Tim Mediasi DriveO DIY)",
            "renterRefundAmount": 125000, "rentalPayoutAmount": 25000,
            "reasoning": "Berdasarkan perbandingan citra resolusi tinggi saat serah terima vs pengembalian, goresan minor sudah ada 70% di awal. Kompromi adil: Biaya poles ringan Rp 25.000 dialokasikan ke mitra, sisa deposit Rp 125.000 langsung dicairkan ke rekening penyewa.",
        },
    },
]

NOTIFICATIONS = [
    {"id": "notif-1", "title": "Dana DP Berhasil Masuk ke Rekening Penampung (Escrow)",
     "message": "Pembayaran DP sebesar Rp 465.000 untuk Toyota Innova Zenix telah aman ditampung di escrow PT DriveO Nusantara.",
     "category": "TRANSAKSI", "timestamp": "2026-10-05T08:15:00+07:00", "is_read": False,
     "link_url": "/booking/bk-zenix-demo-01"},
    {"id": "notif-2", "title": "Pengingat Jadwal Serah Terima Kendaraan H-1",
     "message": "Armada Honda Brio RS Anda dijadwalkan siap diserahterimakan besok pukul 08:00 WIB di Pintu Selatan Stasiun Tugu.",
     "category": "OPERASIONAL", "timestamp": "2026-10-04T12:00:00+07:00", "is_read": False,
     "link_url": "/booking/bk-active-demo-03"},
    {"id": "notif-3", "title": "Verifikasi e-KYC KTP & SIM A Berhasil Disetujui",
     "message": "Profil Anda telah berstatus Terverifikasi Penuh. Anda sekarang memenuhi syarat untuk menyewa mobil lepas kunci di seluruh mitra Yogyakarta.",
     "category": "KEAMANAN", "timestamp": "2026-10-03T10:30:00+07:00", "is_read": True,
     "link_url": "/akun/verifikasi"},
    {"id": "notif-4", "title": "Pembaruan Kasus Sengketa #DSP-202610-0089",
     "message": "Tim Mediasi DriveO telah mengeluarkan putusan mediasi independen terkait klaim deposit jaminan Anda.",
     "category": "SENGKETA", "timestamp": "2026-10-05T09:05:00+07:00", "is_read": False,
     "link_url": "/sengketa/dsp-demo-01"},
]


def _parse_iso(val):
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(val)


# Demo users mirroring frontend SAMPLE_USERS (password: password123)
DEMO_USERS = [
    {"email": "budi.santoso@gmail.com", "name": "Budi Santoso", "phone": "081234567890", "role": UserRole.PENYEWA},
    {"email": "owner@tugurentjogja.com", "name": "Agus Pramono", "phone": "081223344550", "role": UserRole.RENTAL},
    {"email": "ops@tugurentjogja.com", "name": "Rizky Ramadhan", "phone": "081298765432", "role": UserRole.STAFF_OPERASIONAL},
    {"email": "finance@tugurentjogja.com", "name": "Ratna Sari", "phone": "081377889900", "role": UserRole.STAFF_KEUANGAN},
    {"email": "admin@driveo.id", "name": "Super Admin DriveO", "phone": "081100001111", "role": UserRole.ADMIN},
    {"email": "verifikasi@driveo.id", "name": "Dewi Lestari", "phone": "081122223333", "role": UserRole.TIM_VERIFIKASI},
    {"email": "cs@driveo.id", "name": "Bayu Prasetyo", "phone": "081144445555", "role": UserRole.CUSTOMER_SUPPORT},
    {"email": "mediasi@driveo.id", "name": "Haryo Yudistira", "phone": "081166667777", "role": UserRole.TIM_MEDIASI},
]
DEMO_USER_PASSWORD = "password123"


async def seed_data(session: AsyncSession) -> None:
    settings = get_settings()

    # Idempotency check via admin user
    result = await session.execute(select(User).where(User.email == "admin@driveo.com"))
    if result.scalars().first():
        return

    print("Seeding database (full marketplace demo)...")

    # --- Roles ---
    role_admin = await get_or_create_role(session, UserRole.ADMIN)
    await get_or_create_role(session, UserRole.RENTAL)
    await get_or_create_role(session, UserRole.PENYEWA)

    # --- Admin user ---
    if settings.seed_admin_password:
        admin = User(
            id=new_id(), email="admin@driveo.com",
            password_hash=hash_password(settings.seed_admin_password), role_id=role_admin.id,
        )
        session.add(admin)

    # --- Pickup spots ---
    for spot in PICKUP_SPOTS:
        session.add(m.PickupSpot(**spot))

    # --- Marketplace rentals ---
    for r in RENTALS:
        session.add(m.MarketplaceRental(**r))

    # --- Marketplace vehicles (public catalog) ---
    for v in VEHICLES:
        session.add(m.MarketplaceVehicle(**v))

    # --- Mitra fleet vehicles (owned by rental-tugu) ---
    for v in MITRA_VEHICLES:
        session.add(m.MarketplaceVehicle(**v))

    # --- Disputes ---
    for d in DISPUTES:
        row = dict(d)
        row["created_at"] = _parse_iso(row["created_at"])
        session.add(m.Dispute(**row))

    # --- In-app notifications ---
    for n in NOTIFICATIONS:
        row = dict(n)
        row["timestamp"] = _parse_iso(row["timestamp"])
        session.add(m.InAppNotification(**row))

    # --- Demo users ---
    for u in DEMO_USERS:
        role = await get_or_create_role(session, u["role"])
        demo_user = User(
            id=new_id(),
            email=u["email"],
            name=u["name"],
            phone=u["phone"],
            password_hash=hash_password(DEMO_USER_PASSWORD),
            role_id=role.id,
        )
        session.add(demo_user)

    await session.commit()
    print("Seeding complete.")


if __name__ == "__main__":
    from app.core.database import async_session

    async def run():
        async with async_session() as session:
            await seed_data(session)

    asyncio.run(run())
