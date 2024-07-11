from clients.slack_onboarding import OnboardingTutorial


def test_welcome_block():
    assert OnboardingTutorial.WELCOME_BLOCK == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Welcome to AgriKnowledge Hub!*",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Get reliable farming information, learn new techniques,"
                    "and connect with experts for quick tips. Our goal is to"
                    "help you achieve higher productivity and incomes."
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "To get started, please tell us:"
                    "\n• Your name"
                    "\n• Your country"
                    "\n• The crops you grow"
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Together, we can enhance your farming success!",
            },
        },
    ]


def test_divider_block():
    assert OnboardingTutorial.DIVIDER_BLOCK == {"type": "divider"}


def test_init():
    channel = "test_channel"
    onboarding_tutorial = OnboardingTutorial(channel)
    assert onboarding_tutorial.channel == channel
    assert onboarding_tutorial.timestamp == ""


def test_get_message_payload():
    channel = "test_channel"
    onboarding_tutorial = OnboardingTutorial(channel)
    payload = onboarding_tutorial.get_message_payload()
    assert payload["ts"] == ""
    assert payload["channel"] == channel
    assert payload["blocks"] == [
        {"type": "divider"},
        *OnboardingTutorial.WELCOME_BLOCK,
        {"type": "divider"},
    ]
