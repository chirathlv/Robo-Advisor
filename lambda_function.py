### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response

def data_validation(age, investment_amount, intent_request):
    '''
    Validate user inputs
    '''

    # User's Age validation
    if age is not None:
        age = parse_int(age)

        # Checking if the user's Age is less than 65 
        if age >= 65:
            return build_validation_result(
                False,
                "age",
                "You should be below 65 years old to use this service, "
                "please provide a different age",
            )

        # Checking if the user entered invalid minus age
        if age <= 0:
            return build_validation_result(
                False,
                "age",
                "You age should not be a zero or a Negative value, "
                "please provide a different age",
            )

    # Investment Amount validation
    if investment_amount is not None:
        investment_amount = parse_int(investment_amount)

        if investment_amount < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "The investment amount should be equal to or great than 5000, "
                "please provide a different amount",
            )

    # True results is returned if age or investment_amount are valid
    return build_validation_result(True, None, None)

### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt
        # for the first violation detected.

        # Get all the slots
        slots = get_slots(intent_request)

        # data_validation function for user input validation
        validation_results = data_validation(age, investment_amount, intent_request)

        # If user input invalid validation, then elicitSlot dialog action being used to re-prompt for the user at first hand
        if not validation_results["isValid"]:
            slots[validation_results["violatedSlot"]] = None # Clearing up for re-enter

            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_results["violatedSlot"],
                validation_results["message"],
            )

        # Fetch current session attibutes
        output_session_attributes = intent_request["sessionAttributes"]

        return delegate(output_session_attributes, get_slots(intent_request))

    # Get the initial investment recommendation

    if risk_level == "Very Low":
        initial_recommendation = "80% bonds (AGG), 20% equities (SPY)"
    elif risk_level == "Low":
        initial_recommendation = "60% bonds (AGG), 40% equities (SPY)"
    elif risk_level == "Medium":
        initial_recommendation = "40% bonds (AGG), 60% equities (SPY)"
    elif risk_level == "High":
        initial_recommendation = "20% bonds (AGG), 80% equities (SPY)"
    elif risk_level == "Very High":
        initial_recommendation = "20% bonds (AGG), 80% equities (SPY)"
    else:
        initial_recommendation = "100% bonds (AGG), 0% equities (SPY)"

    # Return a message with the initial recommendation based on the risk level.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """{} thank you for your information;
            based on the risk level you defined, my recommendation is to choose an investment portfolio with {}
            """.format(
                first_name, initial_recommendation
            ),
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "RecommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)
