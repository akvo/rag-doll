#!/bin/bash

# How to use: ./invite_to_twilio.sh "phone_number1" "phone_number2" "phone_number_etc"

# Default message
MESSAGE_BODY="Hi! To register your phone number with Twilio, please reply to this message with: join fly-handle."

# Twilio API endpoint and credentials
TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
TWILIO_WHATSAPP_NUMBER=${TWILIO_WHATSAPP_NUMBER}
FROM_PHONE_NUMBER="whatsapp:$TWILIO_WHATSAPP_NUMBER"

# Loop through each phone number provided as arguments
for TO_PHONE_NUMBER in "$@"; do
    # Send whatsapp message
    curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Messages.json" \
    --data-urlencode "To=whatsapp:$TO_PHONE_NUMBER" \
    --data-urlencode "From=$FROM_PHONE_NUMBER" \
    --data-urlencode "Body=$MESSAGE_BODY" \
    -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN"

    echo "Message sent to $TO_PHONE_NUMBER"
done
