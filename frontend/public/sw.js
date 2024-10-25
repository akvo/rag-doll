self.addEventListener("push", function (event) {
  const data = event.data.json();
  const title = data.title;
  const options = {
    body: data.body,
    // TODO :: change the icon
    // icon: "/images/whisper-logo.png",
  };

  event.waitUntil(self.registration.showNotification(title, options));
});
