from config.db import SessionLocal
from models.db import StockItem


SEED = [
    # ---------------- ENGINE OIL ----------------
    dict(
        category="engine_oil",
        brand="Castrol",
        spec_text="vw 504.00, vw 507.00, porsche c30",
        viscosity="5w-30",
        size="5L",
        price=8500,
        quantity=12,
    ),
    dict(
        category="engine_oil",
        brand="Castrol",
        spec_text="vw 504.00, vw 507.00, porsche c30",
        viscosity="5w-30",
        size="1L",
        price=1900,
        quantity=40,
    ),
    dict(
        category="engine_oil",
        brand="Total",
        spec_text="renault rn0720, renault rn17",
        viscosity="5w-30",
        size="5L",
        price=7200,
        quantity=8,
    ),
    dict(
        category="engine_oil",
        brand="Mobil",
        spec_text="bmw ll-04, mb 229.51",
        viscosity="5w-30",
        size="5L",
        price=9200,
        quantity=5,
    ),

    # ---------------- GEARBOX OIL ----------------
    dict(
        category="gearbox_oil",
        brand="Febi",
        spec_text="vw g 052 171 a2, vw g 052 512 a2, mtf lt-2",
        viscosity="75w-80",
        size="1L",
        price=2300,
        quantity=15,
    ),
    dict(
        category="gearbox_oil",
        brand="Motul",
        spec_text="renault nfj, renault nfx",
        viscosity="75w-80",
        size="2L",
        price=4100,
        quantity=6,
    ),
    dict(
        category="gearbox_oil",
        brand="Mannol",
        spec_text="api gl-4, mb 235.10, vw g 052 178 a2",
        viscosity="75w-90",
        size="1L",
        price=1800,
        quantity=20,
    ),

    # ---------------- OIL FILTER ----------------
    dict(
        category="oil_filter",
        brand="Purflux",
        spec_text="purflux ls946, mann w 7032, bosch f 026 407 176, oem 8200768913",
        viscosity=None,
        size="1 pc",
        price=1400,
        quantity=25,
    ),
    dict(
        category="oil_filter",
        brand="Mann",
        spec_text="mann w 68/3, purflux ls743, oem 90915-yzzj1",
        viscosity=None,
        size="1 pc",
        price=1200,
        quantity=30,
    ),
    dict(
        category="oil_filter",
        brand="Bosch",
        spec_text="bosch f 026 407 176, oem 03n115562b",
        viscosity=None,
        size="1 pc",
        price=1600,
        quantity=18,
    ),
    dict(
        category="oil_filter",
        brand="Purflux",
        spec_text="purflux ls924, oem 1109.ay, oem 1109.c1",
        viscosity=None,
        size="1 pc",
        price=1350,
        quantity=22,
    ),
]


def seed():
    with SessionLocal() as s:
        existing = s.query(StockItem).count()
        if existing:
            print(f"Table already has {existing} rows. Aborting to avoid duplicates.")
            return
        for row in SEED:
            s.add(StockItem(**row))
        s.commit()
        print(f"Inserted {len(SEED)} rows.")


if __name__ == "__main__":
    seed()