from fastapi import FastAPI
from app.api import auth, routes, users, admin, bookings

app = FastAPI(
    title="Aventón API",
    description="Backend para la aplicación de carpooling Aventón.",
    version="0.1.0",
)
app.include_router(routes.router, prefix="/routes", tags=["Routes"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenido a la API de Aventón"}
