from agent.db_tools.stock_lookup import _query_engine_oil , _query_filter , _query_gearbox_oil , _serialize

from config.db import SessionLocal

session = SessionLocal()

result1=_query_engine_oil(session , "vw 507.00" , "5w-30")



for item in result1:
    print(_serialize(item)) 

