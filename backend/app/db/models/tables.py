
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import BaseDB
from sqlalchemy import String, Integer, Numeric, Text, Index

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func



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

    image_front_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_back_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    
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

    image_front_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_back_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class Filter_Item(BaseDB):
    __tablename__ = "Filter_items"
    __table_args__ = (
     )
    
    id: Mapped[int] = mapped_column(primary_key=True)

    brand: Mapped[str] = mapped_column(String(64), index=True)     

    reference: Mapped[str] = mapped_column(Text, index=True)

   
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0, index=True)    #how many items do we have in the stock 

    image_front_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_back_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

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

    image_front_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_back_url: Mapped[str | None] = mapped_column(String(512), nullable=True)



# these ones not for the stock , but kind of cache for the models and there exact target 
class Oil_Engine_Cache(BaseDB):
    __tablename__ = "oil_engine_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    model: Mapped[str] = mapped_column(Text, index=True)

    start_year: Mapped[int] = mapped_column(Integer())
    end_year: Mapped[int] = mapped_column(Integer())

    engine: Mapped[str] = mapped_column(Text, index=True)     # single engine variant
    fuel_type: Mapped[str] = mapped_column(String(64), index=True)

    viscosity: Mapped[str] = mapped_column(String(16), index=True, nullable=True)
    capacity_liters: Mapped[str] = mapped_column(String(16), nullable=True)
    oem: Mapped[str] = mapped_column(Text, index=True)        # single spec
    api_acea: Mapped[str] = mapped_column(Text, index=True)


class Transmission_Oil_Cache(BaseDB):
    __tablename__ = "transmission_oil_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    model: Mapped[str] = mapped_column(Text, index=True)

    start_year: Mapped[int] = mapped_column(Integer())
    end_year: Mapped[int] = mapped_column(Integer())

    gearbox: Mapped[str] = mapped_column(Text, index=True)    # single gearbox ref
    transmission_type: Mapped[str] = mapped_column(String(64), index=True)

    viscosity: Mapped[str] = mapped_column(String(16), index=True, nullable=True)
    capacity_liters: Mapped[str] = mapped_column(String(16), nullable=True)
    oem: Mapped[str] = mapped_column(Text, index=True)







class Order(BaseDB):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    customer_name: Mapped[str] = mapped_column(String(128))
    customer_phone: Mapped[str] = mapped_column(String(32), index=True)
    customer_email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    wilaya: Mapped[str] = mapped_column(String(64), index=True)
    city: Mapped[str] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    total: Mapped[float] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)


class OrderItem(BaseDB):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)

    category: Mapped[str] = mapped_column(String(32))
    product_id: Mapped[int] = mapped_column(Integer)

    # Frozen values at order time — see note below
    brand_snapshot: Mapped[str] = mapped_column(String(64))
    name_snapshot: Mapped[str] = mapped_column(String(255))
    specification_snapshot: Mapped[str] = mapped_column(Text)
    size_snapshot: Mapped[str | None] = mapped_column(String(32), nullable=True)
    unit_price_snapshot: Mapped[float] = mapped_column(Numeric(10, 2))

    quantity: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[float] = mapped_column(Numeric(12, 2))
    