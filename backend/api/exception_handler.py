"""Custom exception handler for DRF."""
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    NotFound,
    MethodNotAllowed
)
from django.http import Http404


def custom_exception_handler(exc, context):
    """
    Process DRF exceptions to specific formats.

    Ensures that error responses follow the specific structures:
    - {"errors": ...} for 400, 403, 404, 405 status codes.
    - {"detail": ...} for 401 status codes.
    """
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            if isinstance(response.data, dict):
                if ('detail' in response.data and
                        len(response.data) == 1 and
                        isinstance(response.data['detail'], str)):
                    response.data = {'errors': response.data['detail']}
                elif 'errors' not in response.data:
                    response.data = {'errors': response.data}
            elif isinstance(response.data, list) and \
                    all(isinstance(item, str) for item in response.data):
                response.data = {'errors': response.data}
            elif isinstance(response.data, str):
                response.data = {'errors': response.data}

        elif isinstance(exc, (NotFound, MethodNotAllowed, Http404)):
            error_message = str(exc.detail if hasattr(exc, 'detail') and
                                exc.detail else exc)
            if ('detail' in response.data and
                    isinstance(response.data['detail'], str)):
                error_message = response.data['detail']
            response.data = {'errors': error_message}

        elif response.status_code == 401:
            current_message = None
            if ('detail' in response.data and
                    isinstance(response.data['detail'], str)):
                current_message = response.data['detail']
            elif 'errors' in response.data:
                current_message = str(response.data['errors'])
            elif isinstance(response.data, str):
                current_message = response.data
            else:
                current_message = str(exc.detail if hasattr(exc, 'detail') and \
                                      exc.detail else exc)
            response.data = {'detail': current_message}

        elif response.status_code == 400 and isinstance(exc, APIException):
            error_message = str(exc.detail if hasattr(exc, 'detail') and \
                                exc.detail else exc)
            if ('detail' in response.data and
                    isinstance(response.data['detail'], str)):
                error_message = response.data['detail']

            if not (isinstance(response.data, dict) and 'errors'
                    in response.data):
                response.data = {'errors': error_message}

        elif response.status_code in [400, 403, 404, 405] and \
                not (isinstance(response.data, dict) and
                     ('errors' in response.data or
                      'detail' in response.data)):
            if isinstance(response.data, (dict, list)):
                response.data = {'errors': response.data}
            else:
                response.data = {'errors': str(response.data)}

    return response
