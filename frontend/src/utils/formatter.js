export const createQueueMessage = ({
  messageId,
  conversationId,
  clientPhoneNumber,
  userPhoneNumber,
  sender,
  body,
  media = null,
  context = null,
  transformationLog = null,
}) => {
  if (media === null) {
    media = [];
  }
  if (context === null) {
    context = [];
  }
  if (transformationLog === null) {
    transformationLog = [body];
  }

  const message = {
    conversation_envelope: {
      message_id: messageId,
      conversation_id: conversationId,
      client_phone_number: clientPhoneNumber,
      user_phone_number: userPhoneNumber,
      sender: sender,
    },
    body: body,
    media: media,
    context: context,
    transformation_log: transformationLog,
  };

  return message;
};
