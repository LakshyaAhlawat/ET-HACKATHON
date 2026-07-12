from fastapi import FastAPI

from app.api import cascade, compliance, sld

app = FastAPI(title="EPC Project Intelligence")

app.include_router(compliance.router)
app.include_router(cascade.router)
app.include_router(sld.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
