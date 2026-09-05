from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1 import auth, master_data, journal_entries, sales, purchase, dashboard, reports, portal

app = FastAPI(title="Urban Furniture Accounting System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(master_data.router)
app.include_router(journal_entries.router)
app.include_router(sales.router)
app.include_router(purchase.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(portal.router)


@app.exception_handler(IntegrityError)
def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "A record with conflicting or duplicate data already exists."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
