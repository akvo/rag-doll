export const setCookie = (name, value, days = 2) => {
  const expires = new Date(
    Date.now() + days * 24 * 60 * 60 * 1000
  ).toUTCString();
  document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Strict; Secure;`;
};

export const getCookie = (name) => {
  const cookieArr = document.cookie.split(";");
  for (let i = 0; i < cookieArr.length; i++) {
    const cookiePair = cookieArr[i].split("=");
    if (name === cookiePair[0].trim()) {
      return decodeURIComponent(cookiePair[1]);
    }
  }
  return null;
};

export const deleteCookie = (name) => {
  // Unregister service worker
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .getRegistrations()
      .then((registrations) => {
        for (let registration of registrations) {
          registration.unregister().then((success) => {
            if (success) {
              console.log("Service Worker unregistered");
            }
          });
        }
      })
      .catch((error) => {
        console.error("Error unregistering service worker:", error);
      });
  }
  // EOL unregister service worker

  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Strict;`;
};
