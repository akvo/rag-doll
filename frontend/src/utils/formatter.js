const formatDateToISOString = (date) => {
  // UTC format
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0"); // Months are zero-indexed
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  const seconds = String(date.getUTCSeconds()).padStart(2, "0");
  const milliseconds = String(date.getUTCMilliseconds()).padStart(3, "0");

  const microseconds = milliseconds.padEnd(6, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}.${microseconds}+00:00`;
};

export const generateMessage = ({
  message_id,
  client_phone_number,
  sender_role,
  body,
  platform,
  chat_session_id = null,
  timestamp = null,
  media = null,
  context = null,
  transformation_log = null,
}) => {
  if (media === null) {
    media = [];
  }
  if (context === null) {
    context = [];
  }
  if (transformation_log === null) {
    transformation_log = [body];
  }
  if (timestamp === null) {
    const now = new Date();
    const formattedDate = formatDateToISOString(now);
    timestamp = formattedDate;
  }

  const message = {
    conversation_envelope: {
      chat_session_id: chat_session_id,
      message_id: message_id,
      client_phone_number: client_phone_number,
      sender_role: sender_role,
      platform: platform,
      timestamp: timestamp,
    },
    body: body,
    media: media,
    context: context,
    transformation_log: transformation_log,
  };

  return message;
};

export const formatChatTime = (timeString) => {
  const tz = timeString && timeString.includes("+00:00") ? "" : "+00:00";
  const date = new Date(`${timeString}${tz}`);

  const browserTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
    timeZone: browserTimeZone,
  });
};

export const trimMessage = (text, maxLength = 90) => {
  if (text.length > maxLength) {
    return text.slice(0, maxLength) + "...";
  }
  return text;
};
