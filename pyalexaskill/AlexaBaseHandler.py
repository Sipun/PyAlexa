import abc
import logging


class AlexaBaseHandler(object):
    """
    Base class for a python Alexa Skill Set.  Concrete implementations
    are expected to implement the abstract methods.

    See the following for Alexa details:
    https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/handling-requests-sent-by-alexa
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, app_id=None):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.app_id = app_id

    @abc.abstractmethod
    def on_launch(self, launch_request, session):
        """
        Implement the LaunchRequest.  Called when the user issues a:
        Alexa, open <invocation name>
        :param launch_request:
        :param session:
        :return: the output of _build_response
        """
        pass

    @abc.abstractmethod
    def on_session_started(self, session_started_request, session):
        pass

    @abc.abstractmethod
    def on_intent(self, intent_request, session):
        """
        Implement the IntentRequest
        :param intent_request:
        :param session:
        :return: the output of _build_response
        """
        pass

    @abc.abstractmethod
    def on_help_intent(self, intent_request, session):
        """
        Implement the built in help intent.
        :param intent_request:
        :param session:
        :return:
        """
        raise ValueError("Help Intent was not implemented")

    @abc.abstractmethod
    def on_stop_intent(self, intent_request, session):
        """
        Implement the built in stop intent.
        :param intent_request:
        :param session:
        :return:
        """
        raise ValueError("Stop Intent was not implemented")

    @abc.abstractmethod
    def on_cancel_intent(self, intent_request, session):
        """
        Implement the built in cancel intent.
        :param intent_request:
        :param session:
        :return:
        """
        raise ValueError("Cancel Intent was not implemented")

    @abc.abstractmethod
    def on_no_intent(self, intent_request, session):
        """
        Implement the built in no (or negative) intent.
        :param intent_request:
        :param session:
        :return:
        """
        raise ValueError("Answer No Intent was not implemented")

    @abc.abstractmethod
    def on_yes_intent(self, intent_request, session):
        """
        Implement the built in yes (or positive) intent.
        :param intent_request:
        :param session:
        :return:
        """
        raise ValueError("Answer Yes Intent was not implemented")

    @abc.abstractmethod
    def on_repeat_intent(self, intent_request, session):
        """
        Implement the built in repeat intent.
        :param intent_request:
        :param session:
        :return:
        """
        raise ValueError("Answer Repeat Intent was not implemented")

    @abc.abstractmethod
    def on_start_over_intent(self, intent_request, session):
        """
        Implement the built in start over intent.
        :param intent_request:
        :param session:
        :return:
        """
        raise ValueError("Start Over Intent was not implemented")

    @abc.abstractmethod
    def on_session_ended(self, session_end_request, session):
        """
        Implement the SessionEndRequest
        :param session_end_request:
        :param session:
        :return: the output of _build_response
        """
        pass

    @abc.abstractmethod
    def on_processing_error(self, event, context, exc):
        """
        If an unexpected error occurs during the process_request method
        this handler will be invoked to give the concrete handler
        an opportunity to respond gracefully

        :param exc exception instance
        :return: the output of _build_response
        """
        pass

    def process_request(self, event, context):
        """
        Helper method to process the input Alexa request and
        dispatch to the appropriate on_ handler
        :param event:
        :param context:
        :return: response from the on_ handler
        """
        # if its a new session, run the new session code
        try:
            if(self.app_id and event['session']['application']['applicationId'] != self.app_id):
                raise ValueError("Invalid Application ID")

            response = None
            if event['session']['new']:
                self.on_session_started({'requestId': event['request']['requestId']}, event['session'])

                # regardless of whether its new, handle the request type
            if event['request']['type'] == "LaunchRequest":
                response = self.on_launch(event['request'], event['session'])
            elif event['request']['type'] == "IntentRequest":
                intent_name = self._get_intent_name(event['request'])
                if intent_name == "AMAZON.HelpIntent":
                    response = self.on_help_intent(event['request'],event['session'])
                elif intent_name == "AMAZON.StopIntent":
                    response = self.on_stop_intent(event['request'], event['session'])
                elif intent_name == "AMAZON.CancelIntent":
                    response = self.on_cancel_intent(event['request'], event['session'])
                elif intent_name == "AMAZON.NoIntent":
                    response = self.on_no_intent(event['request'], event['session'])
                elif intent_name == "AMAZON.RepeatIntent":
                    response = self.on_repeat_intent(event['request'], event['session'])
                elif intent_name == "AMAZON.StartOverIntent":
                    response = self.on_start_over_intent(event['request'], event['session'])
                elif intent_name == "AMAZON.YesIntent":
                    response = self.on_yes_intent(event['request'], event['session'])
                else:
                    response = self.on_intent(event['request'], event['session'])
            elif event['request']['type'] == "SessionEndedRequest":
                response = self.on_session_ended(event['request'], event['session'])

        except Exception as exc:
            self.logger.error(exc.message)
            response = self.on_processing_error(event, context, exc)

        return response

    # --------------- Helpers that build all of the responses ----------------------
    def _build_speechlet_response(self, card_title, card_output, speech_output, reprompt_text, should_end_session):
        """
        Internal helper method to build the speechlet portion of the response
        :param card_title:
        :param card_output:
        :param speech_output:
        :param reprompt_text:
        :param should_end_session:
        :return:
        """
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': speech_output
            },
            'card': {
                'type': 'Simple',
                'title': card_title,
                'content': card_output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }

    def _build_response(self, session_attributes, speechlet_response):
        """
        Internal helper method to build the Alexa response message
        :param session_attributes:
        :param speechlet_response:
        :return: properly formatted Alexa response
        """
        return {
            'version': '1.0',
            'sessionAttributes': session_attributes,
            'response': speechlet_response
        }

    def _is_intent(self, intent_name, intent_request):
        return self._get_intent_name(intent_request) == intent_name

    def _get_intent(self, intent_request):
        if 'intent' in intent_request:
            return intent_request['intent']
        else:
            return None

    def _get_intent_name(self, intent_request):
        intent = self._get_intent(intent_request)
        intent_name = None
        if intent is not None and 'name' in intent:
            intent_name = intent['name']

        return intent_name

    def _slot_exists(self, slot_name, intent_request):
        intent = self._get_intent(intent_request)
        if intent is not None:
            return slot_name in intent['slots']
        else:
            return False

    def _get_slot_value(self, slot_name, intent_request):
        value = None
        try:
            if self._slot_exists(slot_name, intent_request):
                intent = self._get_intent(intent_request)
                value = intent['slots'][slot_name]['value']
            else:
                value = None
        except Exception as exc:
            self.logger.error("Error getting slot value for slot_name={0}".format(slot_name))

        return value
