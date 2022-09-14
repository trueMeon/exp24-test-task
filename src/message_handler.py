from __future__ import annotations
from typing import List, Optional
from src.message_services import MessageServiceBase, MessageServiceException, TelegramMessageService, \
    WhatsAppMessageService, PushMessageService
from src.utils import MessagedException


# Available service types
SERVICE_TELEGRAM = 'telegram'
SERVICE_WHATSAPP = 'whatsapp'
SERVICE_PUSH = 'push'


class MessageHandlerException(MessagedException):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MessageException(MessagedException):
    def __init__(self, message: str) -> None:
        super().__init__(message)


# It can have constructor's parameters for a message service creation
# For instance, to pass logger instance to services 
# But now we don't need any parameters for this
class MessageServiceFactory(object):
    def create_service(self, service_type: str) -> MessageServiceBase:
        if service_type == SERVICE_TELEGRAM:
            return TelegramMessageService()
        elif service_type == SERVICE_WHATSAPP:
            return WhatsAppMessageService()
        elif service_type == SERVICE_PUSH:
            return PushMessageService()

        raise MessageHandlerException('Wrong type of service is given')


# The input facade context. It is implemented like a builder
# In the original task it's called Payload
class MessageHandlerRequest(object):
    def __init__(self) -> None:
        self._batch = []
        self._type = ''

    def get_list(self) -> List[str]:
        return self._batch

    def get_type(self) -> str:
        return self._type

    def set_service_type(self, service_type: str) -> MessageHandlerRequest:
        assert type(service_type) == str

        self._type = service_type
        return self

    def append_message(self, message: str) -> MessageHandlerRequest:
        self._batch.append(message)
        return self

    def append_messages(self, messages: List[str]) -> MessageHandlerRequest:
        self._batch.extend(messages)
        return self

    def clear_messages(self) -> MessageHandlerRequest:
        self._batch.clear()
        return self


class MessageStatus(object):
    def __init__(self, original_message: str, transformed_message: str, error: Optional[MessageException]) -> None:
        self._original_message = original_message
        self._transformed_message = transformed_message
        self._error = error

    def get_original_message(self) -> str:
        return self._original_message

    def get_transformed_message(self) -> str:
        return self._transformed_message

    def get_error(self) -> Optional[MessageException]:
        return self._error

    def is_sent(self) -> bool:
        return self._error is None


# The output facade context
# In the original task it's called Payload
class MessageHandlerResponse(object):
    def __init__(self, request: MessageHandlerRequest, message_statuses: List[MessageStatus]) -> None:
        self._request = request
        self._message_statuses = message_statuses
        self._messages_are_sent = len([s for s in message_statuses if s.is_sent()])

    def messages_are_sent(self) -> int:
        return self._messages_are_sent

    def message_statuses(self) -> List[MessageStatus]:
        return self._message_statuses
    
    def get_request(self) -> MessageHandlerRequest:
        return self._request


# Facade
# Responsible for input redirection to requested message service and wrapping of results
class MessageHandler(object):
    def __init__(self, services_factory: MessageServiceFactory) -> None:
        assert issubclass(type(services_factory), MessageServiceFactory)
        self._factory = services_factory
    
    def handle(self, request: MessageHandlerRequest) -> MessageHandlerResponse:
        assert type(request) == MessageHandlerRequest

        service = self._factory.create_service(request.get_type())

        if not issubclass(type(service), MessageServiceBase):
            raise MessageHandlerException('Wrong type of service is given')

        result = service.send(request.get_list())
        statuses = [MessageStatus(orig_mess, trans_mess, self._convert_exception(err)) for (orig_mess, trans_mess, err) in result]
        return MessageHandlerResponse(request, statuses)
    
    def _convert_exception(self, exception: Optional[MessageServiceException]) -> Optional[MessageException]:
        return MessageException(exception.message) if exception is not None else None
