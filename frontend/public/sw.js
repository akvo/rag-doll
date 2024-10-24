self.addEventListener("push", function (event) {
  const data = event.data.json();
  const title = data.title;
  const options = {
    body: data.body,
    icon: "/images/whisper-logo.png", // Path to your icon
  };

  event.waitUntil(self.registration.showNotification(title, options));
});
