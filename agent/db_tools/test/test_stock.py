# agent/db_tools/test_specs.py
from db_tools.spec_lookup import specs_lookup
from config.db import SessionLocal
from models.db import Oil_Engine_Cache


# seed one row so you can test
with SessionLocal() as s:
    if s.query(Oil_Engine_Cache).count() == 0:
        s.add(Oil_Engine_Cache(
            brand="Renault", model="Clio IV",
            start_year=2012, end_year=2019,
            engine="K9K 646", fuel_type="diesel",
            viscosity="5w-30", capacity_liters="4.5",
            oem="renault rn0720", api_acea="acea c4",
        ))
        s.commit()

print(specs_lookup.invoke({
    "fluid_type": "Engine Oil",
    "brand": "Renault", "model": "Clio IV", "year": 2016,
    "engine": "1.5 dCi 110",
}))