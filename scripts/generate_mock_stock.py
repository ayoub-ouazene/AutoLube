# scripts/seed_stock.py
"""
Seed the stock tables with mock data for development.

Usage:
    python -m scripts.seed_stock          # insert if empty
    python -m scripts.seed_stock --reset  # wipe existing rows first
"""

import sys
from config.db import SessionLocal
from models.db import Oil_Engine_Item, Oil_Transmission_Item


ENGINE_OIL_STOCK = [
    # ---------- VW 504.00 / 507.00 (VAG diesel + petrol, DPF-safe) ----------
    dict(brand="Castrol", oem="vw 504.00, vw 507.00, porsche c30",
         api_acea="acea c3", viscosity="5w-30", size="1L",
         price=1900, quantity=40),
    dict(brand="Castrol", oem="vw 504.00, vw 507.00, porsche c30",
         api_acea="acea c3", viscosity="5w-30", size="5L",
         price=8500, quantity=12),
    dict(brand="Mobil", oem="vw 504.00, vw 507.00",
         api_acea="acea c3", viscosity="5w-30", size="5L",
         price=9200, quantity=5),
    dict(brand="Total", oem="vw 504.00, vw 507.00",
         api_acea="acea c3", viscosity="0w-30", size="5L",
         price=9800, quantity=6),

    # ---------- Renault RN0720 / RN17 (dCi with DPF) ----------
    dict(brand="Total", oem="renault rn0720, renault rn17",
         api_acea="acea c4", viscosity="5w-30", size="5L",
         price=7200, quantity=8),
    dict(brand="Elf", oem="renault rn0720, renault rn17",
         api_acea="acea c4", viscosity="5w-30", size="5L",
         price=6800, quantity=10),
    dict(brand="Elf", oem="renault rn0720",
         api_acea="acea c4", viscosity="5w-30", size="1L",
         price=1600, quantity=30),

    # ---------- PSA B71 2290 / B71 2312 (PSA diesel with FAP) ----------
    dict(brand="Total", oem="psa b71 2290, psa b71 2312",
         api_acea="acea c2", viscosity="5w-30", size="5L",
         price=7500, quantity=7),
    dict(brand="Motul", oem="psa b71 2290, psa b71 2312",
         api_acea="acea c2", viscosity="0w-30", size="5L",
         price=8800, quantity=4),

    # ---------- BMW LL-04 / MB 229.51 ----------
    dict(brand="Mobil", oem="bmw ll-04, mb 229.51",
         api_acea="acea c3", viscosity="5w-30", size="5L",
         price=9200, quantity=5),
    dict(brand="Castrol", oem="bmw ll-04, mb 229.51",
         api_acea="acea c3", viscosity="0w-30", size="1L",
         price=2200, quantity=20),

    # ---------- Universal / no DPF (older petrol) ----------
    dict(brand="Total", oem="api sn",
         api_acea="api sn, acea a3/b4", viscosity="5w-40", size="5L",
         price=5500, quantity=15),
    dict(brand="Mannol", oem="api sn",
         api_acea="api sn, acea a3/b4", viscosity="10w-40", size="5L",
         price=4200, quantity=25),
]


GEARBOX_OIL_STOCK = [
    # ---------- VW G 052 171 A2 (MQ200 / MQ250 manual) ----------
    dict(brand="Febi", oem="vw g 052 171 a2, vw g 052 512 a2, mtf lt-2",
         viscosity="75w-80", size="1L", price=2300, quantity=15),
    dict(brand="Febi", oem="vw g 052 171 a2, vw g 052 512 a2, mtf lt-2",
         viscosity="75w-80", size="2L", price=4400, quantity=6),

    # ---------- VW G 052 178 A2 (0AF / some MQ200 variants) ----------
    dict(brand="Mannol", oem="vw g 052 178 a2, mb 235.10, api gl-4",
         viscosity="75w-90", size="1L", price=1800, quantity=20),

    # ---------- Renault NFJ / NFX (TL4, JR5 manual) ----------
    dict(brand="Motul", oem="renault nfj, renault nfx",
         viscosity="75w-80", size="2L", price=4100, quantity=6),
    dict(brand="Elf", oem="renault nfj, renault nfx",
         viscosity="75w-80", size="1L", price=2000, quantity=18),

    # ---------- PSA / generic manual gearbox ----------
    dict(brand="Total", oem="psa 9730.a1, api gl-4",
         viscosity="75w-80", size="1L", price=2200, quantity=12),
    dict(brand="Total", oem="psa 9730.a1, api gl-4",
         viscosity="75w-80", size="2L", price=4200, quantity=5),

    # ---------- Generic GL-4 / GL-5 (older manuals, differential) ----------
    dict(brand="Mannol", oem="api gl-4",
         viscosity="75w-90", size="1L", price=1600, quantity=30),
    dict(brand="Mannol", oem="api gl-5, mb 235.0",
         viscosity="80w-90", size="1L", price=1700, quantity=25),
    dict(brand="Castrol", oem="api gl-4, api gl-5",
         viscosity="75w-90", size="1L", price=2500, quantity=14),

    # ---------- Toyota LV / Honda MTF ----------
    dict(brand="Toyota", oem="toyota lv, api gl-4",
         viscosity="75w-90", size="1L", price=2800, quantity=8),
]


def seed(reset: bool = False):
    with SessionLocal() as s:
        if reset:
            print("Deleting existing rows...")
            s.query(Oil_Engine_Item).delete()
            s.query(Oil_Transmission_Item).delete()
            s.commit()

        existing_engine = s.query(Oil_Engine_Item).count()
        existing_trans = s.query(Oil_Transmission_Item).count()

        if existing_engine or existing_trans:
            print(f"Tables already populated "
                  f"(engine={existing_engine}, transmission={existing_trans}). "
                  f"Use --reset to wipe first.")
            return

        for row in ENGINE_OIL_STOCK:
            s.add(Oil_Engine_Item(**row))
        for row in GEARBOX_OIL_STOCK:
            s.add(Oil_Transmission_Item(**row))
        s.commit()

        print(f"Inserted {len(ENGINE_OIL_STOCK)} engine-oil rows.")
        print(f"Inserted {len(GEARBOX_OIL_STOCK)} gearbox-oil rows.")


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)