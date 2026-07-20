from pydantic import BaseModel, Field
from typing import List, Optional

class InvoiceSchema(BaseModel):
    invoice_number: str = Field(description="Unique identifier of the invoice.")
    vendor: str = Field(description="Vendor name.")
    amount: Optional[float] = Field(None, description="Total invoice amount.")
    date: Optional[str] = Field(None, description="Invoice date.")

class OrderSheetSchema(BaseModel):
    po_number: str = Field(description="Purchase Order number.")
    vendor: str = Field(description="Vendor name.")
    order_quantity: int = Field(description="Total order quantity.")
    ship_date: str = Field(description="Shipping deadline date.")

class TechPackSchema(BaseModel):
    style_number: str = Field(description="Unique style number identifier.")
    season: str = Field(description="Garment season designation.")
    brand: str = Field(description="Brand name.")
    materials: List[str] = Field(default_factory=list, description="List of materials utilized.")
    colors: List[str] = Field(default_factory=list, description="List of colors specified.")
