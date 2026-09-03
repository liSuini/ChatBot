class ChatBotException(Exception):
    """统一业务异常基类，携带 error_code + message + HTTP status"""

    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class LLMProviderError(ChatBotException):
    def __init__(self, message: str = "LLM 调用失败"):
        super().__init__("LLM_ERROR", message, 502)


class NotFoundError(ChatBotException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__("NOT_FOUND", message, 404)


class ForbiddenError(ChatBotException):
    def __init__(self, message: str = "无权访问该资源"):
        super().__init__("FORBIDDEN", message, 403)
