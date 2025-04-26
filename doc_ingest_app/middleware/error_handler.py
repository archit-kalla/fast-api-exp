from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the exception here if needed
            return JSONResponse(
                status_code=500,
                content={"detail": "An unexpected error occurred.",
                         "error": str(exc) if str(exc) else "Unknown error"})
