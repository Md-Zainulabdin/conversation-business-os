from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.ai import router as ai_router
from app.routes.auth import router as auth_router
from app.routes.categories import router as categories_router
from app.routes.customers import router as customers_router
from app.routes.expenses import router as expenses_router
from app.routes.products import router as products_router
from app.routes.purchases import router as purchases_router
from app.routes.sales import router as sales_router
from app.routes.stats import router as stats_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(categories_router)
app.include_router(customers_router)
app.include_router(expenses_router)
app.include_router(products_router)
app.include_router(purchases_router)
app.include_router(sales_router)
app.include_router(stats_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
