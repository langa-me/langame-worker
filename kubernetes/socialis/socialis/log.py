"""Interceptor that log."""

import grpc


class RequestLoggerInterceptor(grpc.ServerInterceptor):
    """
    TODO
    """

    def __init__(self, logger, verbose=False):
        super().__init__()
        self._logger = logger
        self._verbose = verbose

    def intercept_service(self, continuation, handler_call_details):
        self._logger.info(
            f"Received request: {handler_call_details.method} "
            + f"{handler_call_details.invocation_metadata}"
            if self._verbose
            else ""
        )
