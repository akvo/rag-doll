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
                *self.WELCOME_BLOCK,
                self.DIVIDER_BLOCK,
                *self._get_reaction_block(),
                self.DIVIDER_BLOCK,
                *self._get_pin_block(),
            ],
        }

    def _get_reaction_block(self):
        task_checkmark = self._get_checkmark(self.reaction_task_completed)
        text = (
            f"{task_checkmark} *Add an emoji reaction to this message*"
            "You can quickly respond to any message on Slack with an emoji."
            "Reactions can be used for any purposes."
        )
        return self._get_task_block(text)

    def _get_pin_block(self):
        task_checkmark = self._get_checkmark(self.pin_task_completed)
        text = (
            f"{task_checkmark} *Pin this message* :round_pushpin:\n"
            "Important messages and files can be pinned to the details pane in "
            "any channel or direct message, including group messages, "
            "for easy reference."
        )
        return self._get_task_block(text)

    @staticmethod
    def _get_checkmark(task_completed: bool) -> str:
        if task_completed:
            return ":white_check_mark:"
        return ":white_large_square:"

    @staticmethod
    def _get_task_block(text):
        return [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        ]
