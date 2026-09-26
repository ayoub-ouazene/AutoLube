# scripts/seed_cache.py
"""
Seed the specs cache tables with mock data.

Usage:
    python -m scripts.seed_cache          # insert if empty
    python -m scripts.seed_cache --reset  # wipe existing rows first
"""

import sys
from app.db.session import SessionLocal
from app.db.models.tables import Oil_Engine_Cache, Transmission_Oil_Cache


# One row = one engine variant. If two engines share the same spec, two rows.
ENGINE_CACHE = [
    # ---------------- Renault Clio IV ----------------
    dict(brand="Renault", model="Clio IV", start_year=2012, end_year=2019,
         engine="K9K 646", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.5",
         oem="renault rn0720", api_acea="acea c4"),
    dict(brand="Renault", model="Clio IV", start_year=2012, end_year=2019,
         engine="K9K 608", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.5",
         oem="renault rn0720", api_acea="acea c4"),
    dict(brand="Renault", model="Clio IV", start_year=2012, end_year=2019,
         engine="K9K 612", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.5",
         oem="renault rn0720", api_acea="acea c4"),
    dict(brand="Renault", model="Clio IV", start_year=2012, end_year=2019,
         engine="H4B 400", fuel_type="petrol",
         viscosity="5w-30", capacity_liters="4.2",
         oem="renault rn0700", api_acea="acea c3"),
    dict(brand="Renault", model="Clio IV", start_year=2012, end_year=2019,
         engine="H4B 412", fuel_type="petrol",
         viscosity="5w-30", capacity_liters="4.2",
         oem="renault rn0700", api_acea="acea c3"),

    # ---------------- Dacia Duster ----------------
    dict(brand="Dacia", model="Duster", start_year=2010, end_year=2017,
         engine="K9K 892", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.5",
         oem="renault rn0720", api_acea="acea c4"),
    dict(brand="Dacia", model="Duster", start_year=2010, end_year=2017,
         engine="K4M 690", fuel_type="petrol",
         viscosity="5w-40", capacity_liters="4.8",
         oem="renault rn0700", api_acea="acea a3/b4"),
    dict(brand="Dacia", model="Duster", start_year=2018, end_year=2023,
         engine="K9K 656", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.5",
         oem="renault rn0720", api_acea="acea c4"),
    dict(brand="Dacia", model="Duster", start_year=2018, end_year=2023,
         engine="H5H 470", fuel_type="petrol",
         viscosity="5w-30", capacity_liters="4.5",
         oem="renault rn17", api_acea="acea c3"),

    # ---------------- Peugeot 208 ----------------
    dict(brand="Peugeot", model="208", start_year=2012, end_year=2019,
         engine="DV6FD", fuel_type="diesel",
         viscosity="0w-30", capacity_liters="3.8",
         oem="psa b71 2312", api_acea="acea c2"),
    dict(brand="Peugeot", model="208", start_year=2012, end_year=2019,
         engine="DV6FE", fuel_type="diesel",
         viscosity="0w-30", capacity_liters="3.8",
         oem="psa b71 2312", api_acea="acea c2"),
    dict(brand="Peugeot", model="208", start_year=2012, end_year=2019,
         engine="EB2F", fuel_type="petrol",
         viscosity="0w-30", capacity_liters="3.5",
         oem="psa b71 2312", api_acea="acea c2"),
    dict(brand="Peugeot", model="208", start_year=2012, end_year=2019,
         engine="EP6FDT", fuel_type="petrol",
         viscosity="5w-30", capacity_liters="4.2",
         oem="psa b71 2290", api_acea="acea c2"),

    # ---------------- CitroÃ«n C3 II ----------------
    dict(brand="CitroÃ«n", model="C3 II", start_year=2009, end_year=2016,
         engine="DV4TD", fuel_type="diesel",
         viscosity="0w-30", capacity_liters="3.8",
         oem="psa b71 2312", api_acea="acea c2"),
    dict(brand="CitroÃ«n", model="C3 II", start_year=2009, end_year=2016,
         engine="DV6DTED", fuel_type="diesel",
         viscosity="0w-30", capacity_liters="3.8",
         oem="psa b71 2312", api_acea="acea c2"),
    dict(brand="CitroÃ«n", model="C3 II", start_year=2009, end_year=2016,
         engine="EB2F", fuel_type="petrol",
         viscosity="0w-30", capacity_liters="3.5",
         oem="psa b71 2312", api_acea="acea c2"),

    # ---------------- VW Golf VII ----------------
    dict(brand="Volkswagen", model="Golf VII", start_year=2012, end_year=2020,
         engine="CRKB", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.3",
         oem="vw 507.00", api_acea="acea c3"),
    dict(brand="Volkswagen", model="Golf VII", start_year=2012, end_year=2020,
         engine="DDYA", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.3",
         oem="vw 507.00", api_acea="acea c3"),
    dict(brand="Volkswagen", model="Golf VII", start_year=2012, end_year=2020,
         engine="CJZA", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.3",
         oem="vw 507.00", api_acea="acea c3"),
    dict(brand="Volkswagen", model="Golf VII", start_year=2012, end_year=2020,
         engine="CHPA", fuel_type="petrol",
         viscosity="5w-30", capacity_liters="4.0",
         oem="vw 504.00", api_acea="acea c3"),

    # ---------------- VW Golf VI ----------------
    dict(brand="Volkswagen", model="Golf VI", start_year=2008, end_year=2012,
         engine="CAYC", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.3",
         oem="vw 507.00", api_acea="acea c3"),
    dict(brand="Volkswagen", model="Golf VI", start_year=2008, end_year=2012,
         engine="CBDC", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.3",
         oem="vw 507.00", api_acea="acea c3"),

    # ---------------- Audi A3 8V ----------------
    dict(brand="Audi", model="A3 8V", start_year=2012, end_year=2020,
         engine="CRBC", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.7",
         oem="vw 507.00", api_acea="acea c3"),
    dict(brand="Audi", model="A3 8V", start_year=2012, end_year=2020,
         engine="CUNA", fuel_type="diesel",
         viscosity="5w-30", capacity_liters="4.7",
         oem="vw 507.00", api_acea="acea c3"),
    dict(brand="Audi", model="A3 8V", start_year=2012, end_year=2020,
         engine="CJSA", fuel_type="petrol",
         viscosity="5w-30", capacity_liters="4.5",
         oem="vw 504.00", api_acea="acea c3"),

    # ---------------- Toyota Yaris ----------------
    dict(brand="Toyota", model="Yaris", start_year=2011, end_year=2020,
         engine="1KR-FE", fuel_type="petrol",
         viscosity="0w-20", capacity_liters="3.4",
         oem="toyota api sp", api_acea="api sp, ilsac gf-6"),
    dict(brand="Toyota", model="Yaris", start_year=2011, end_year=2020,
         engine="1NR-FE", fuel_type="petrol",
         viscosity="0w-20", capacity_liters="3.4",
         oem="toyota api sp", api_acea="api sp, ilsac gf-6"),
]


TRANSMISSION_CACHE = [
    # ---------------- VW MQ200 / MQ250 (manual) ----------------
    dict(brand="Volkswagen", model="Golf VII", start_year=2012, end_year=2020,
         gearbox="MQ200", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.0",
         oem="vw g 052 171 a2"),
    dict(brand="Volkswagen", model="Golf VII", start_year=2012, end_year=2020,
         gearbox="MQ250", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.1",
         oem="vw g 052 171 a2"),

    dict(brand="Volkswagen", model="Golf VI", start_year=2008, end_year=2012,
         gearbox="MQ200", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.0",
         oem="vw g 052 171 a2"),
    dict(brand="Volkswagen", model="Golf VI", start_year=2008, end_year=2012,
         gearbox="MQ250", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.1",
         oem="vw g 052 171 a2"),

    dict(brand="Audi", model="A3 8P", start_year=2003, end_year=2013,
         gearbox="MQ250", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.1",
         oem="vw g 052 171 a2"),

    # ---------------- VW DSG ----------------
    dict(brand="Volkswagen", model="Golf VII", start_year=2012, end_year=2020,
         gearbox="DQ200", transmission_type="DSG/DCT",
         viscosity="", capacity_liters="1.7",
         oem="vw g 052 182 a2"),
    dict(brand="Volkswagen", model="Golf VII", start_year=2012, end_year=2020,
         gearbox="DQ250", transmission_type="DSG/DCT",
         viscosity="", capacity_liters="6.0",
         oem="vw g 052 182 a2"),

    # ---------------- Renault TL4 / JR5 (manual) ----------------
    dict(brand="Renault", model="Clio IV", start_year=2012, end_year=2019,
         gearbox="TL4", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.3",
         oem="renault nfj"),
    dict(brand="Renault", model="Clio IV", start_year=2012, end_year=2019,
         gearbox="JR5", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.0",
         oem="renault nfj"),

    dict(brand="Dacia", model="Duster", start_year=2010, end_year=2017,
         gearbox="TL4", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.3",
         oem="renault nfj"),
    dict(brand="Dacia", model="Duster", start_year=2018, end_year=2023,
         gearbox="TL4", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.3",
         oem="renault nfj"),

    # ---------------- PSA MA5 / BE4 (manual) ----------------
    dict(brand="Peugeot", model="208", start_year=2012, end_year=2019,
         gearbox="MA5", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.0",
         oem="psa 9730.a1"),
    dict(brand="CitroÃ«n", model="C3 II", start_year=2009, end_year=2016,
         gearbox="MA5", transmission_type="Manual",
         viscosity="75w-80", capacity_liters="2.0",
         oem="psa 9730.a1"),

    # ---------------- Toyota C56 (manual) ----------------
    dict(brand="Toyota", model="Yaris", start_year=2011, end_year=2020,
         gearbox="C56", transmission_type="Manual",
         viscosity="75w-90", capacity_liters="1.9",
         oem="toyota lv"),
]


def seed(reset: bool = False):
    with SessionLocal() as s:
        if reset:
            print("Deleting existing rows...")
            s.query(Oil_Engine_Cache).delete()
            s.query(Transmission_Oil_Cache).delete()
            s.commit()

        existing_engine = s.query(Oil_Engine_Cache).count()
        existing_trans = s.query(Transmission_Oil_Cache).count()

        if existing_engine or existing_trans:
            print(f"Tables already populated "
                  f"(engine_cache={existing_engine}, transmission_cache={existing_trans}). "
                  f"Use --reset to wipe first.")
            return

        for row in ENGINE_CACHE:
            s.add(Oil_Engine_Cache(**row))
        for row in TRANSMISSION_CACHE:
            s.add(Transmission_Oil_Cache(**row))
        s.commit()

        print(f"Inserted {len(ENGINE_CACHE)} engine-cache rows.")
        print(f"Inserted {len(TRANSMISSION_CACHE)} transmission-cache rows.")


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)