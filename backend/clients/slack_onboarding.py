class OnboardingTutorial:
    WELCOME_BLOCK = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Welcome to AgriKnowledge Hub!*"
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

    DIVIDER_BLOCK = {"type": "divider"}

    def __init__(self, channel):
        self.channel = channel
        self.timestamp = ""

    def get_message_payload(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "blocks": [
                self.DIVIDER_BLOCK,
                *self.WELCOME_BLOCK,
                self.DIVIDER_BLOCK,
            ],
        }
