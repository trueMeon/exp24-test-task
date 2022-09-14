from typing import List
from collections import defaultdict
import unittest
from src.message_services import MessageServiceBase
from src.message_handler import SERVICE_TELEGRAM, SERVICE_WHATSAPP, SERVICE_PUSH, \
    MessageHandler, MessageHandlerException, MessageHandlerRequest, MessageHandlerResponse, MessageServiceFactory


class HandlerCreationTest(unittest.TestCase):
    def test_normal_factory(self):
        MessageHandler(MessageServiceFactory())

    def test_not_allowed_type_factory(self):
        factories = [0, '', None]
        for (i, factory) in enumerate(factories):
            with self.subTest(i=i):
                with self.assertRaises(Exception):
                    MessageHandler(factory)


class MessageRequestTest(unittest.TestCase):
    def test_normal_service_type(self):
        MessageHandlerRequest().set_service_type('serviceType')

    def test_invalid_service_type(self):
        invalid_service_types = [0, None]
        for (i, service) in enumerate(invalid_service_types):
            with self.subTest(i=i):
                with self.assertRaises(AssertionError):
                    MessageHandlerRequest().set_service_type(service)


class HandlerTest(unittest.TestCase):
    def setUp(self):
        self.handler = MessageHandler(MessageServiceFactory())

    def test_normal_send(self):
        services = [SERVICE_TELEGRAM, SERVICE_WHATSAPP, SERVICE_PUSH]
        for (i, service) in enumerate(services):
            with self.subTest(i=i):
                request = MessageHandlerRequest()\
                    .set_service_type(service)\
                    .append_message('Test0')\
                    .append_messages(['Test1', 'Test2'])

                response = self.handler.handle(request)
                self.assertEqual(response.messages_are_sent(),
                                 len(request.get_list()))

    def test_invalid_request_type(self):
        invalid_requests = [0, '', None]
        for (i, request) in enumerate(invalid_requests):
            with self.subTest(i=i):
                with self.assertRaises(AssertionError):
                    self.handler.handle(request)

    def test_invalid_service(self):
        request = MessageHandlerRequest()\
            .set_service_type('invalid-service123')\
            .append_message('Test0')\
            .append_messages(['Test1', 'Test2'])

        with self.assertRaises(MessageHandlerException):
            self.handler.handle(request)

    def test_corrupted_service_factory(self):
        class CorruptedServiceFactory(MessageServiceFactory):
            def create_service(self, type: str) -> MessageServiceBase:
                return None

        handler = MessageHandler(CorruptedServiceFactory())
        request = MessageHandlerRequest()\
            .set_service_type(SERVICE_TELEGRAM)\
            .append_message('Test0')\
            .append_messages(['Test1', 'Test2'])

        with self.assertRaises(MessageHandlerException):
            handler.handle(request)

    def test_invalid_messages(self):
        invalid_messages = [0, None, {}, []]

        for (i, message) in enumerate(invalid_messages):
            request = MessageHandlerRequest()\
                .set_service_type(SERVICE_TELEGRAM)\
                .append_message(message)
            
            with self.subTest(i=i):
                with self.assertRaises(AssertionError):
                    self.handler.handle(request)

    def test_result(self):
        params = [
            # Specifically for TelegramMessageService validator
            (SERVICE_TELEGRAM, ['Test0', 'Test1', 'Test2', '*Test0',
             'Test*1', 'Test2*', ';Test0', 'Test;1', 'Test2;'], []),
            # Specifically for WhatsAppMessageService validator
            (SERVICE_WHATSAPP, ['Test0', 'Test1', 'Test2', ';Test0', 'Test;1', 
             'Test2;'], ['*Test0', 'Test*1', 'Test2*']),
            # Specifically for PushMessageService validator
            (SERVICE_PUSH, ['Test0', 'Test1', 'Test2', '*Test0',
             'Test*1', 'Test2*'], [';Test0', 'Test;1', 'Test2;']),
        ]

        for (i, (service, valid_messages, invalid_messages)) in enumerate(params):
            request = MessageHandlerRequest()\
                .set_service_type(service)\
                .append_messages(valid_messages)\
                .append_messages(invalid_messages)

            with self.subTest(i=i):
                response = self.handler.handle(request)
                self.assertTrue(self.do_valid_and_invalid_messages_match(
                    response, valid_messages, invalid_messages))

    def do_valid_and_invalid_messages_match(self, response: MessageHandlerResponse,
                                            valid_messages: List[str], invalid_messages: List[str]) -> bool:

        if response.messages_are_sent() != len(valid_messages):
            return False

        if len(response.message_statuses()) != len(valid_messages) + len(invalid_messages):
            return False

        (sent_count, not_sent_count) = (0, 0)
        (sent_messages, not_sent_messages) = (
            defaultdict(int), defaultdict(int))

        for message_status in response.message_statuses():
            message = message_status.get_original_message()

            if message_status.is_sent():
                sent_count += 1
                sent_messages[message] += 1
            else:
                not_sent_count += 1
                not_sent_messages[message] += 1

        if sent_count != len(valid_messages) or not_sent_count != len(invalid_messages):
            return False

        for valid_message in valid_messages:
            if sent_messages[valid_message] == 0:
                return False

            sent_messages[valid_message] -= 1

        for invalid_message in invalid_messages:
            if not_sent_messages[invalid_message] == 0:
                return False

            not_sent_messages[invalid_message] -= 1

        return True
