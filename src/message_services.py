from abc import abstractmethod
from typing import List, Optional, Tuple
import logging
from src.utils import MessagedException


# Abstract classes and interfaces


class MessageServiceException(MessagedException):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MessageValidation(MessagedException):
    def __init__(self, message: str) -> None:
        super().__init__(message)


# Responsible for message validation and transformation into specific appropriate form
class MessageServiceBase(object):
    def send(self, messages: List[str]) -> List[Tuple[str, str, Optional[MessageServiceException]]]:
        assert len([m for m in messages if type(m) != str]) == 0

        logging.debug('[MessageService] %s messages are going to send', len(messages))

        validated_messages = [(x, self._validate(x)) for x in messages]
        appropriate_messages = [mess for (mess, err) in validated_messages if err is None]

        logging.debug('[MessageService] %s messages discarded for sending during validation', 
                        len(messages) - len(appropriate_messages))

        send_result = self._send([self._transform(mess) for mess in appropriate_messages])
        result = [(orig_mess, trans_mess, err) for (orig_mess, (trans_mess, err)) in zip(appropriate_messages, send_result)]

        logging.debug('[MessageService] %s messages from %s have been sent successfully', 
                        len([_ for (_, _, err) in result if err is None]), 
                        len(appropriate_messages))

        result.extend([(mess, mess, err) for (mess, err) in validated_messages if err is not None])

        return result

    def _transform(self, message: str) -> str:
        return message

    def _validate(self, message: str) -> Optional[MessageServiceException]:
        return None

    # Must keep input message order for output
    @abstractmethod
    def _send(self, messages: List[str]) -> List[Tuple[str, Optional[MessageServiceException]]]:
        pass


# Implementation

# To respect the Single-Resposibility Principle we need a message sender 
# for every type of message service for remote service interaction.
# And all credentials about interaction have to be there.
# Since MessageServiceBase responsible only for the messages validation and 
# transformation but not for interaction with remote services.
# But here I'm just gonna mock the implementation of sending.


class TelegramMessageService(MessageServiceBase):
    def __init__(self) -> None:
        super().__init__()

    # Must call remote sender service here
    # But now let's assume that every message will be sent successfully
    # And there will be no error
    def _send(self, messages: List[str]) -> List[Tuple[str, Optional[MessageServiceException]]]:
        logging.debug('[TelegramMessageService] A batch of %s messages has been sent', len(messages))
        logging.debug('[TelegramMessageService] Batch content: %s', " | ".join(messages))

        return [(x, None) for x in messages]

    # Removes bullets from message on test purposes
    def _transform(self, message: str) -> str:
        return message.replace('*', '')


class WhatsAppMessageService(MessageServiceBase):
    def __init__(self) -> None:
        super().__init__()

    # Must call remote sender service here
    # But now let's assume that every message will be sent successfully
    # And there will be no error
    def _send(self, messages: List[str]) -> List[Tuple[str, Optional[MessageServiceException]]]:
        for mess in messages:
            logging.debug('[WhatsAppMessageService] "%s" message has been sent', mess)

        return [(x, None) for x in messages]

    # On test purposes
    # Removes exclamation marks from message
    def _transform(self, message: str) -> str:
        return message.replace('!', '')

    # On test purposes
    # Doesn't pass message if it contains bullet signs
    def _validate(self, message: str) -> Optional[MessageServiceException]:
        return MessageValidation('Bullets in the text are not allowed') if '*' in message else None 


class PushMessageService(MessageServiceBase):
    def __init__(self) -> None:
        super().__init__()

    # Must call remote sender service here
    # But now let's assume that every message will be sent successfully
    # And there will be no error
    def _send(self, messages: List[str]) -> List[Tuple[str, Optional[MessageServiceException]]]:
        for mess in messages:
            logging.debug('[PushMessageService] "%s" message has been sent', mess)

        return [(x, None) for x in messages]
    
    # On test purposes
    # Removes question marks from message
    def _transform(self, message: str) -> str:
        return message.replace('?', '')

    # On test purposes
    # Doesn't pass message if it contains semicolumn signs
    def _validate(self, message: str) -> Optional[MessageServiceException]:
        return MessageValidation('Semicolumn in the text are not allowed') if ';' in message else None
