from rest_framework import status
from rest_framework.exceptions import APIException


class PayloadTooLarge(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "The file is too large."
    default_code = "file_too_large"


class UnsupportedResumeType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = "Only PDF and Word (.docx) files are accepted."
    default_code = "unsupported_file_type"


class UnreadableResume(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The resume file could not be read."
    default_code = "unreadable_file"
