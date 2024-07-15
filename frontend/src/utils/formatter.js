export const generateMessage = ({
  message_id,
  client_phone_number,
  sender_role,
  body,
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

  const message = {
    conversation_envelope: {
      message_id: message_id,
      client_phone_number: client_phone_number,
      sender_role: sender_role,
      timestamp: timestamp,
    },
    body: body,
    media: media,
    context: context,
    transformation_log: transformation_log,
  };

  return message;
};
