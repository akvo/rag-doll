class OnboardingTutorial:
    """
    Constructs the onboarding message and stores the
    state of which tasks were completed.
    """
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
        self.username = "wgprtm_slackbot"
        self.icon_emoji = ":robot_face:"
        self.timestamp = ""
        self.reaction_task_completed = False
        self.pin_task_completed = False

    def get_message_payload(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": [
                self.DIVIDER_BLOCK,
                *self.WELCOME_BLOCK,
                self.DIVIDER_BLOCK,
            ],
        }
