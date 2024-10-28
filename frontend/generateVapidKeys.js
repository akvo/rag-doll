const webPush = require("web-push");

const vapidKeys = webPush.generateVAPIDKeys();

const envData = `
NEXT_PUBLIC_VAPID_PUBLIC_KEY=${vapidKeys.publicKey}
NEXT_PUBLIC_VAPID_PRIVATE_KEY=${vapidKeys.privateKey}
`;

console.info(envData);
