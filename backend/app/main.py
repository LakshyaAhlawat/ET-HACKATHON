from fastapi import FastAPI

from app.api import cascade, compliance, graph, query, rfi, sld, verify

app = FastAPI(title="EPC Project Intelligence")

app.include_router(compliance.router)
app.include_router(cascade.router)
app.include_router(sld.router)
app.include_router(verify.router)
app.include_router(graph.router)
app.include_router(query.router)
app.include_router(rfi.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
