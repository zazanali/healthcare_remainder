from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.config import settings

from app.routes import reminders
from app.services.scheduler import scheduler_startup, scheduler_shutdown
from app.utils.logging import configure_logging, set_request_id
from uuid import uuid4

configure_logging(settings.LOG_LEVEL)

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["method", "path"])

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_startup()
    yield
    scheduler_shutdown()

app = FastAPI(
    title="Healthcare Reminders & Alerts",
    version="2.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Authentication operations"},
        {"name": "reminders", "description": "Reminder operations"},
    ],
    openapi_version="3.1.0",
)

# Add JWT security scheme
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security scheme for JWT
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    
    # Ensure components object exists
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter the token with the `Bearer: ` prefix",
        }
    }
    
    # Apply security globally to all operations
    openapi_schema["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

from app.routes import auth
app.include_router(auth.router, prefix="/auth", tags=["auth"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id_and_metrics(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or str(uuid4())
    set_request_id(rid)
    method = request.method
    path = request.url.path
    with LATENCY.labels(method, path).time():
        response = await call_next(request)
    REQUESTS.labels(method, path, str(response.status_code)).inc()
    response.headers["X-Request-ID"] = rid
    return response

@app.get('/')
def home():
    return {'message': 'Welcome to Healthcare Reminders & Alerts API using FastAPI for EvaHealthAI App'}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(reminders.router, prefix="", tags=["reminders"])