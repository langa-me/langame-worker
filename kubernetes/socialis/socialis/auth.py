"""Interceptor that ensures a specific header is present."""

import grpc
from firebase_admin.auth import (
    verify_id_token,
    InvalidIdTokenError,
    ExpiredIdTokenError,
    RevokedIdTokenError,
    CertificateFetchError,
    UserDisabledError,
)


def _unary_unary_rpc_terminator(code, details):
    def terminate(ignored_request, context):
        context.abort(code, details)

    return grpc.unary_unary_rpc_method_handler(terminate)


class RequestHeaderValidatorInterceptor(grpc.ServerInterceptor):
    """
    TODO
    """

    def __init__(self, header, value, code, details, logger):
        super().__init__()
        self._header = header
        self._value = value
        self._terminator = _unary_unary_rpc_terminator(code, details)
        self._logger = logger

    def intercept_service(self, continuation, handler_call_details):
        # find value of bearer
        id_token = [
            v for k, v in handler_call_details.invocation_metadata if k == self._header
        ]
        
        if not id_token:
            self._logger.warning(
                f"No {self._header} header found in request"
            )
            return self._terminator
        id_token = id_token[0].replace("bearer ", "")
        try:
            decoded_token = verify_id_token(id_token)
            uid = decoded_token["uid"]
            self._logger.info(f"User {uid} authenticated")
            return continuation(handler_call_details)
        except (
            ValueError,
            InvalidIdTokenError,
            ExpiredIdTokenError,
            RevokedIdTokenError,
            CertificateFetchError,
            UserDisabledError,
        ) as e:
            self._logger.warning(f"{e}")
            return self._terminator
