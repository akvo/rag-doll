#!/usr/bin/env bash

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <message_content> <number_of_messages>"
    exit 1
fi

message_content=$1
number_of_messages=$2
SCHEDULE_TIME="now + 1 minute"
BASE_URL="http://localhost:3001/api/test-rabbitmq-send-message"
LOG_FILE="./send_message.log"
touch $LOG_FILE

send_message() {
    local message=$1
    local index=$2
    echo "Sending message: $message" >> $LOG_FILE
    url="$BASE_URL?message=$(urlencode "$message")"
    curl -s -o /dev/null -w "Message: $message | Status Code: %{http_code} | Time Total: %{time_total}\n" -X 'POST' \
        "$url" \
        -H 'accept: application/json' >> $LOG_FILE 2>&1
    echo "Curl command executed" >> $LOG_FILE
}

schedule_message() {
    local message=$1
    local index=$2
    echo "send_message \"$message\" \"$index\"" | at "$SCHEDULE_TIME" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Message scheduled to be sent at $SCHEDULE_TIME"
        echo "Message scheduled to be sent at $SCHEDULE_TIME" >> $LOG_FILE
        send_message "$message" "$index"  # Call send_message here
    else
        echo "Failed to schedule message"
        echo "Failed to schedule message" >> $LOG_FILE
    fi
}

urlencode() {
    # urlencode <string>
    old_lc_collate=$LC_COLLATE
    LC_COLLATE=C

    local length="${#1}"
    for (( i = 0; i < length; i++ )); do
        local c="${1:$i:1}"
        case $c in
            [a-zA-Z0-9.~_-]) printf '%s' "$c" ;;
            *) printf '%%%02X' "'$c" ;;
        esac
    done

    LC_COLLATE=$old_lc_collate
}

echo "Scheduling $number_of_messages messages with content: $message_content to be sent at $SCHEDULE_TIME"
echo "Scheduling $number_of_messages messages with content: $message_content to be sent at $SCHEDULE_TIME" >> $LOG_FILE

# Repeat for the number of messages specified
for i in $(seq 1 "$number_of_messages"); do
    indexed_message="$message_content - Index: $i"
    schedule_message "$indexed_message" "$i"
done
