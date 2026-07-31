from datetime import datetime

from pydantic import BaseModel


class TransactionItem(BaseModel):
    id: str
    type: str
    reference: str
    entity: str
    amount: float
    status: str
    date: datetime


class OverviewResponse(BaseModel):
    total_sales: float
    stock_items: int
    active_customers: int
    transactions: list[TransactionItem]
