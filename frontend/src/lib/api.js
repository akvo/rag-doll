const baseURL = "/api/";

const initConfig = {
  headers: {
    "Content-Type": "application/json",
  },
};

const API = () => {
  const getConfig = () => {
    return api?.token
      ? {
          ...initConfig,
          headers: {
            ...initConfig.headers,
            Authorization: `Bearer ${api.token}`,
          },
        }
      : initConfig;
  };
  return {
    get: (url, config = {}) =>
      fetch(`${baseURL}${url}`, { ...getConfig(), ...config }),
    post: (url, data, config = {}) =>
      fetch(`${baseURL}${url}`, {
        method: "POST",
        body: data,
        ...getConfig(),
        ...config,
      }),
    put: (url, data, config) =>
      fetch(`${baseURL}${url}`, {
        method: "PUT",
        body: data,
        ...getConfig(),
        ...config,
      }),
    patch: (url, data, config) =>
      fetch(`${baseURL}${url}`, {
        method: "PATCH",
        body: data,
        ...getConfig(),
        ...config,
      }),
    delete: (url) =>
      fetch(`${baseURL}${url}`, { method: "DELETE", ...getConfig() }),
    setToken: (token) => {
      api.token = token;
    },
  };
};

const api = API();

export default api;
