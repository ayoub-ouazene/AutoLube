# scripts/init_db.py
import sys
from app.db.session import engine
from  app.db.models.tables import BaseDB

def init(reset: bool = False):
    if reset:
        print("Dropping all tables...")
        BaseDB.metadata.drop_all(engine)
    print("Creating tables...")
    BaseDB.metadata.create_all(engine)
    print("Done.")

if __name__ == "__main__":
    init(reset="--reset" in sys.argv)