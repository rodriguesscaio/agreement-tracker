from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers import agreements, dashboard, extract

app = FastAPI(
    title="Agreement Tracker",
    description="Extracts structured agreements (who owns what, by when) from pasted or uploaded text.",
    version="0.1.0",
)

app.include_router(extract.router)
app.include_router(agreements.router)
app.include_router(dashboard.router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")
