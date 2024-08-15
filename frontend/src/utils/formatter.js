const formatDateToISOString = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are zero-indexed
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  const milliseconds = String(date.getMilliseconds()).padStart(3, "0");

  // Microseconds are not directly available, so we'll pad the milliseconds to match the desired format
  const microseconds = milliseconds.padEnd(6, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}.${microseconds}`;
};

export const generateMessage = ({
  message_id,
  client_phone_number,
  sender_role,
  body,
  platform,
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
  const now = new Date();

  const diffInMilliseconds = now.getTime() - date.getTime();
  const diffInSeconds = Math.floor(diffInMilliseconds / 1000);

  const minute = 60;
  const hour = minute * 60;
  const day = hour * 24;

  const browserTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  if (diffInSeconds < 5) {
    return "Just now";
  } else if (diffInSeconds < minute) {
    return `${diffInSeconds} seconds ago`;
  } else if (diffInSeconds < hour) {
    const minutes = Math.floor(diffInSeconds / minute);
    return `${minutes} minutes ago`;
  } else if (now.toDateString() === date.toDateString()) {
    return date.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
      timeZone: browserTimeZone,
    });
  } else if (diffInSeconds < day * 2 && now.getDate() !== date.getDate()) {
    return "Yesterday";
  } else {
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
      timeZone: browserTimeZone,
    });
  }
};

export const trimMessage = (text, maxLength = 90) => {
  if (text.length > maxLength) {
    return text.slice(0, maxLength) + "...";
  }
  return text;
};
