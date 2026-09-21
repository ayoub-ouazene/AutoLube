


from sqlalchemy.orm import DeclarativeBase , Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric, Text, Index




class BaseDB(DeclarativeBase):
    pass


class Oil_Engine_Item(BaseDB):
    __tablename__ = "oil_engine_items"
    __table_args__ = (
     )
    
    id: Mapped[int] = mapped_column(primary_key=True)

    brand: Mapped[str] = mapped_column(String(64), index=True)        # "Castrol"


    # Comma-joined OEM specs, stored lowercase for matching
    # e.g. "vw 504.00, vw 507.00, porsche c30"
    oem: Mapped[str] = mapped_column(Text, index=True)

    api_acea: Mapped[str] = mapped_column(Text, index=True)

    # Viscosity grade, lowercase, e.g. "5w-30", "75w-80"
    viscosity: Mapped[str] = mapped_column(String(16), index=True, nullable=True)

   
    

  
    size: Mapped[str] = mapped_column(String(16))     # "5L", "1L"    
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0, index=True)    #how many items do we have in the stock 

    

    
class Oil_Transmission_Item(BaseDB):
    __tablename__ = "transmission_oil_items"
    __table_args__ = (
     )
    
    id: Mapped[int] = mapped_column(primary_key=True)

    brand: Mapped[str] = mapped_column(String(64), index=True)        # "Castrol"
    

    # Comma-joined OEM specs, stored lowercase for matching
    # e.g. "vw 504.00, vw 507.00, porsche c30"
    oem: Mapped[str] = mapped_column(Text, index=True)

    # Viscosity grade, lowercase, e.g. "5w-30", "75w-80"
    viscosity: Mapped[str] = mapped_column(String(16), index=True, nullable=True)

    
    size: Mapped[str] = mapped_column(String(16))     # "5L", "1L"    
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0, index=True)    #how many items do we have in the stock 



class Filter_Item(BaseDB):
    __tablename__ = "Filter_items"
    __table_args__ = (
     )
    
    id: Mapped[int] = mapped_column(primary_key=True)

    brand: Mapped[str] = mapped_column(String(64), index=True)     

    reference: Mapped[str] = mapped_column(Text, index=True)

   
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0, index=True)    #how many items do we have in the stock 



#for liquide de freine , additives , graisse ... 
class Additional_Item(BaseDB):
    __tablename__ = "Additional_items"
    __table_args__ = (
     )
    
    id: Mapped[int] = mapped_column(primary_key=True)

    category_type: Mapped[str] = mapped_column(String(64), index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)     

    reference: Mapped[str] = mapped_column(Text, index=True)


    size: Mapped[str] = mapped_column(String(16))     # "5L", "1L"   
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0, index=True)    #how many items do we have in the stock 




# these ones not for the stock , but kind of cache for the models and there exact target 

class Oil_Engine_Cache(BaseDB):
        __tablename__ = "oil_engine_cache"
        __table_args__ = (
         )
        
        id: Mapped[int] = mapped_column(primary_key=True)
        brand: Mapped[str] = mapped_column(String(64), index=True)        # "Castrol"
        model: Mapped[str] = mapped_column(Text, index=True)

        start_year: Mapped[int] = mapped_column(Integer())
        end_year: Mapped[int] = mapped_column(Integer())

        engine: Mapped[str] = mapped_column(Text, index=True)

        Fuel_type: Mapped[str] = mapped_column(String(64), index=True)   #diesel or petrol 

        # Viscosity grade, lowercase, e.g. "5w-30", "75w-80"
        viscosity: Mapped[str] = mapped_column(String(16), index=True, nullable=True)
        
        oem: Mapped[str] = mapped_column(Text, index=True)
        api_acea: Mapped[str] = mapped_column(Text, index=True)




class Transmission_Oil_Cache(BaseDB):
        __tablename__ = "transmission_oil_cache"
        __table_args__ = (
         )
        
        id: Mapped[int] = mapped_column(primary_key=True)
        brand: Mapped[str] = mapped_column(String(64), index=True)        # "Castrol"
        model: Mapped[str] = mapped_column(Text, index=True)

        start_year: Mapped[int] = mapped_column(Integer())
        end_year: Mapped[int] = mapped_column(Integer())

        gearabox: Mapped[str] = mapped_column(Text, index=True)

        transmission_type: Mapped[str] = mapped_column(String(64), index=True)   #diesel or petrol 

        # Viscosity grade, lowercase, e.g. "5w-30", "75w-80"
        viscosity: Mapped[str] = mapped_column(String(16), index=True, nullable=True)
        
        oem: Mapped[str] = mapped_column(Text, index=True)
        

