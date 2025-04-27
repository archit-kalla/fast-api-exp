from fastapi import FastAPI
from fastapi.responses import JSONResponse

from sqlalchemy.exc import SQLAlchemyError

from .scripts.create_db_schema import create_tables, drop_tables
from .middleware.error_handler import ErrorHandlingMiddleware
from .routes import organizations, users, search, tasks, files, conversations

app = FastAPI()
app.include_router(organizations.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(tasks.router)
app.include_router(files.router)
app.include_router(conversations.router)
# app.add_middleware(ErrorHandlingMiddleware)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    if hasattr(request.state, "session"):
        db_session = request.state.session
        if db_session:
            db_session.rollback()
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred.",
                 "error": str(exc)},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    if hasattr(request.state, "session"):
        db_session = request.state.session
        if db_session:
            db_session.rollback()
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred.",
                 "error": str(exc)},
    )
    
@app.on_event("startup")
def on_startup():
    create_tables()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.delete("/drop_tables", tags=["Admin"])
async def drop_all_tables():
    drop_tables()
    return {"message": "All tables dropped"}

@app.post("/create_tables", tags=["Admin"])
async def create_all_tables():
    create_tables()
    return {"message": "All tables created"}





