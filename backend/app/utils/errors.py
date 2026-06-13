from dataclasses import dataclass


@dataclass
class PublicDataAppError(Exception):
    message: str
    error_code: str


class PublicApiError(PublicDataAppError):
    def __init__(self, message: str = "외부 공공데이터 API 호출에 실패했습니다. 잠시 후 다시 시도해주세요.") -> None:
        super().__init__(message=message, error_code="PUBLIC_API_ERROR")


class MalformedPublicDataError(PublicDataAppError):
    def __init__(self, message: str = "공공데이터 응답 형식이 올바르지 않습니다.") -> None:
        super().__init__(message=message, error_code="MALFORMED_PUBLIC_DATA")


class WidgetTransformError(PublicDataAppError):
    def __init__(self, message: str = "위젯 데이터 변환 중 오류가 발생했습니다.") -> None:
        super().__init__(message=message, error_code="WIDGET_TRANSFORM_ERROR")
