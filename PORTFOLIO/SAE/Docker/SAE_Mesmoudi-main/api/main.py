from fastapi import FastAPI
from routers import membres, publications, equipes, collaboration, simulation

app = FastAPI(
    title="API Bibliométrie LIAS",
    description="API REST d'analyse bibliométrique du laboratoire LIAS — Équipes IDD & SETR (2021–2025)",
    version="1.0.0"
)

@app.get("/", tags=["santé"])
def root():
    return {"message": "API Bibliométrie LIAS opérationnelle 🚀"}

app.include_router(membres.router)
app.include_router(publications.router)
app.include_router(equipes.router)
app.include_router(collaboration.router)
app.include_router(simulation.router)