from httpx import AsyncBaseTransport, Request, Response
from kiota_abstractions.request_option import RequestOption
from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes

from .._version import VERSION
from ..observability_options import ObservabilityOptions
from .middleware import BaseMiddleware
from .options import UserAgentHandlerOption

tracer = trace.get_tracer(ObservabilityOptions.get_tracer_instrumentation_name(), VERSION)


class UserAgentHandler(BaseMiddleware):
    """
    Middleware handler for User Agent.
    """

    def __init__(self, options: RequestOption = UserAgentHandlerOption(), **kwargs):
        super().__init__(**kwargs)
        self.options = UserAgentHandlerOption() if options is None else options

    async def send(self, request: Request, transport: AsyncBaseTransport) -> Response:
        """
        Checks if the request has a User-Agent header and updates it if the
        platform config allows.
        """
        if options := getattr(request, "options", None):
            if parent_span := options.get("parent_span", None):
                _context = trace.set_span_in_context(parent_span)
                _span = tracer.start_span("UserAgentHandler_send", _context)
                if self.options and self.options.is_enabled:
                    _span.set_attribute("com.microsoft.kiota.handler.useragent.enable", True)
                    value = f"{self.options.product_name}/{self.options.product_version}"

                    user_agent = request.headers.get("User-Agent", "")
                    if not user_agent:
                        request.headers.update({"User-Agent": value})
                    else:
                        if value not in user_agent:
                            request.headers.update({"User-Agent": f"{user_agent} {value}"})
                _span.end()

        return await super().send(request, transport)
