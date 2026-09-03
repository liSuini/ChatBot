from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.exceptions import ChatBotException

app = FastAPI(title="ChatBot API", version="0.1.0")


@app.exception_handler(ChatBotException)
async def chatbot_exception_handler(request: Request, exc: ChatBotException):
    """统一业务异常 → JSON 响应 {code, message}"""
    return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})


app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
