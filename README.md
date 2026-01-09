# Aventón - Backend para Aplicación de Carpooling

Este repositorio contiene el backend para **Aventón**, una aplicación de carpooling (carro compartido) donde los conductores publican sus rutas recurrentes y los pasajeros se unen a ellas.

## Estado del Proyecto

El backend es funcional y cuenta con las siguientes características implementadas:

### Funcionalidades Implementadas
-   **Gestión de Usuarios y Autenticación:**
    -   Registro de usuarios mediante **email y contraseña**.
    -   Registro y login mediante **número de teléfono y código OTP** (simulado).
    -   Generación de tokens **JWT** para sesiones seguras.
    -   Roles de usuario (`user`, `admin`).
-   **Gestión de Conductores:**
    -   Registro de vehículos por parte de los conductores.
    -   Creación de rutas con un trazado geoespacial (`LineString`).
-   **Gestión de Pasajeros:**
    -   Búsqueda de rutas geoespacial que pasen cerca de un origen y un destino.
    -   Creación de solicitudes de reserva (`booking`) en estado "pendiente".
-   **Precios y Pagos:**
    -   Modelo de precios dinámico basado en **tarifa por kilómetro**.
    -   Cálculo automático del precio de un viaje basado en la distancia que el pasajero recorrerá sobre la ruta.
    -   Simulación de pago para confirmar una reserva y descontar un asiento.
-   **Administración:**
    -   Endpoint para que un administrador configure la tarifa por kilómetro por defecto del sistema.

## Tech Stack
-   **Framework:** FastAPI
-   **Base de Datos:** PostgreSQL + PostGIS para datos geoespaciales.
-   **ORM:** SQLAlchemy con GeoAlchemy2.
-   **Validación de Datos:** Pydantic
-   **Autenticación:** JWT (JSON Web Tokens)
-   **Hashing de Contraseñas:** Passlib con Bcrypt

---

## Configuración del Entorno de Desarrollo

Sigue estos pasos para levantar el proyecto en un entorno local.

### 1. Prerrequisitos
-   Python 3.11 o superior.
-   PostgreSQL con la extensión PostGIS instalada y en ejecución.

### 2. Instalación
1.  **Clona el repositorio (o usa tu proyecto actual).**

2.  **Crea y activa un entorno virtual:**
    ```bash
    # En Windows
    python -m venv venv
    .\venv\Scripts\activate

    # En macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuración de la Base de Datos
1.  **Conéctate a PostgreSQL** y crea una nueva base de datos.
    ```sql
    CREATE DATABASE aventon;
    ```
2.  **Conéctate a la base de datos `aventon`** (`\c aventon` en `psql`) y ejecuta el script SQL completo que se encuentra más abajo en este mismo `README` para crear todas las tablas, extensiones y tipos de datos necesarios.

### 4. Variables de Entorno
1.  **Crea un archivo `.env`** en la raíz del proyecto.
2.  **Añade las variables de configuración**. Asegúrate de que `DATABASE_URL` coincida con tu configuración de PostgreSQL.

    ```dotenv
    # Reemplaza con tus credenciales y una clave secreta segura
    DATABASE_URL="postgresql://tu_usuario:tu_contraseña@localhost:5432/aventon"
    JWT_SECRET_KEY="una-clave-secreta-muy-larga-y-dificil-de-adivinar"
    ```

### 5. Ejecución
1.  **Inicia el servidor:**
    ```bash
    uvicorn app.main:app --reload
    ```
2.  **Accede a la documentación interactiva** de la API en tu navegador:
    [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Resumen de Endpoints de la API

| Verbo  | Endpoint                               | Descripción                                                              | Autenticación Requerida |
| :----- | :------------------------------------- | :----------------------------------------------------------------------- | :---------------------- |
| `POST` | `/auth/otp/request`                    | Solicita un código OTP para registrarse con un número de teléfono.       | No                      |
| `POST` | `/auth/otp/verify`                     | Valida el OTP y crea/loguea al usuario.                                  | No                      |
| `POST` | `/auth/token`                          | Inicia sesión con email/teléfono y contraseña para obtener un token.     | No                      |
| `GET`  | `/users/me`                            | Obtiene los detalles del usuario autenticado.                            | Sí                      |
| `POST` | `/users/me/vehicles`                   | Registra un nuevo vehículo para el usuario autenticado.                  | Sí                      |
| `GET`  | `/users/me/vehicles`                   | Lista los vehículos del usuario autenticado.                             | Sí                      |
| `POST` | `/routes`                              | Crea una nueva ruta de viaje.                                            | Sí (Conductor)          |
| `GET`  | `/routes/search`                       | Busca rutas que pasen cerca de un origen y destino.                      | Sí (Pasajero)           |
| `POST` | `/bookings`                            | Crea una solicitud de reserva (en estado `pending`).                     | Sí (Pasajero)           |
| `POST` | `/bookings/{booking_id}/pay`           | Simula el pago para confirmar una reserva.                               | Sí (Pasajero)           |
| `PUT`  | `/admin/config`                        | Modifica una configuración del sistema (ej. tarifa por km).              | Sí (Admin)              |

---

## Script de la Base de Datos

Ejecuta este script en tu base de datos `aventon` para crear la estructura completa.

```sql
-- Borrar todo en el orden correcto para evitar errores de dependencias
DROP TABLE IF EXISTS payments, phone_verifications, bookings, route_stops, routes, vehicles, users, system_configs CASCADE;
DROP TYPE IF EXISTS user_role, route_status, booking_status, payment_status;

-- Habilitar extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- Crear tipos ENUM
CREATE TYPE user_role AS ENUM ('user', 'admin');
CREATE TYPE route_status AS ENUM ('active', 'cancelled', 'full', 'completed');
CREATE TYPE booking_status AS ENUM ('pending', 'confirmed', 'cancelled_by_passenger', 'completed');
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');

-- Tabla de Configuraciones del Sistema
CREATE TABLE system_configs (
    key VARCHAR PRIMARY KEY,
    value TEXT NOT NULL
);

-- Insertar tarifa por defecto
INSERT INTO system_configs (key, value) VALUES ('default_price_per_km_cop', '350.0') ON CONFLICT (key) DO NOTHING;

-- Tabla de Usuarios
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR NOT NULL,
    phone_number VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE,
    password_hash VARCHAR,
    profile_picture_url VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    role user_role NOT NULL DEFAULT 'user'
);
CREATE INDEX idx_users_phone_number ON users(phone_number);

-- Tabla de Verificación Telefónica
CREATE TABLE phone_verifications (
    phone_number VARCHAR PRIMARY KEY,
    otp_code VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Tabla de Vehículos
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    brand VARCHAR NOT NULL,
    model VARCHAR NOT NULL,
    color VARCHAR NOT NULL,
    license_plate VARCHAR UNIQUE NOT NULL
);

-- Tabla de Rutas
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_id UUID NOT NULL REFERENCES users(id),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    departure_time TIMESTAMP WITH TIME ZONE NOT NULL,
    estimated_arrival_time TIMESTAMP WITH TIME ZONE NOT NULL,
    available_seats INTEGER NOT NULL CHECK (available_seats >= 0),
    price_per_km DECIMAL(10, 2) NOT NULL,
    is_recurrent BOOLEAN DEFAULT false,
    recurrence_pattern JSONB,
    status route_status DEFAULT 'active',
    path GEOMETRY(LINESTRING, 4326) NOT NULL,
    start_city VARCHAR,
    start_country VARCHAR,
    end_city VARCHAR,
    end_country VARCHAR
);
CREATE INDEX idx_routes_path ON routes USING GIST (path);

-- Tabla de Reservas (Bookings)
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    passenger_id UUID NOT NULL REFERENCES users(id),
    route_id UUID NOT NULL REFERENCES routes(id),
    status booking_status NOT NULL DEFAULT 'pending',
    booked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    pickup_point GEOMETRY(POINT, 4326) NOT NULL,
    dropoff_point GEOMETRY(POINT, 4326) NOT NULL,
    calculated_price DECIMAL(12, 2) NOT NULL
);

-- Tabla de Pagos
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL UNIQUE REFERENCES bookings(id),
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'COP',
    status payment_status NOT NULL DEFAULT 'pending',
    payment_gateway_ref VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);
```
