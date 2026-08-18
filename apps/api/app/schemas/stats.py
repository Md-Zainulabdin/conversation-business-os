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


class DailySalesItem(BaseModel):
    date: str
    amount: float


class LowStockItem(BaseModel):
    id: str
    name: str
    sku: str
    unit: str
    stock_quantity: int
    minimum_stock: int


class TopProductItem(BaseModel):
    name: str
    quantity: int
    revenue: float


class TopCustomerItem(BaseModel):
    name: str
    spend: float


class CategoryBreakdownItem(BaseModel):
    category: str
    amount: float


class OverviewResponse(BaseModel):
    total_sales: float
    expenses_total: float
    profit: float
    stock_items: int
    active_customers: int
    low_stock_count: int
    daily_sales: list[DailySalesItem]
    low_stock: list[LowStockItem]
    top_products: list[TopProductItem]
    top_customers: list[TopCustomerItem]
    category_breakdown: list[CategoryBreakdownItem]
    expense_breakdown: list[CategoryBreakdownItem]
    transactions: list[TransactionItem]