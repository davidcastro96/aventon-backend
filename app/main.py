from fastapi import FastAPI
from app.api import auth, routes, users

app = FastAPI(
    title="Aventón API",
    description="Backend para la aplicación de carpooling Aventón.",
    version="0.1.0",
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(routes.router, prefix="/routes", tags=["Routes"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenido a la API de Aventón"}
