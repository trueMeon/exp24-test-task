import logging
import sys
import os
sys.path.append(os.path.abspath('.'))

from src.message_handler import SERVICE_PUSH, MessageHandler, MessageHandlerRequest, MessageServiceFactory


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.DEBUG)

    handler = MessageHandler(MessageServiceFactory())
    request = MessageHandlerRequest()\
        .set_service_type(SERVICE_PUSH)\
        .append_messages(['Test0', 'Test1', 'Test*1', 'Test0?1', 'Test;123'])

    response = handler.handle(request)

    logging.info('%s messages have been sent', response.messages_are_sent())
    for status in response.message_statuses():
        if status.is_sent():
            logging.info('Original message: %s; Sent: %s', status.get_original_message(), status.get_transformed_message())
        else:
            logging.info('"%s" hasn\'t been sent. Reason: %s', status.get_original_message(), status.get_error().message)
    