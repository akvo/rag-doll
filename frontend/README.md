# Frontend (Next JS)

The frontend of this project is developed using [React with Next.js](https://react.dev/learn/start-a-new-react-project#nextjs-pages-router). In the development environment, the frontend and backend services are configured to facilitate efficient and streamlined development. The frontend, built with React and Next.js, communicates with the backend API using a proxy setup defined in the next.config.js file. This configuration rewrites requests matching the pattern /api/:path* to be forwarded to the backend service at http://backend:5000/api/:path*. This proxy setup simplifies the API call structure during development, allowing developers to interact with the backend as if it were part of the same application.

**Frontend**: http://localhost:3001
**API Docs**: http://localhost:3001/api/docs#/

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://backend:5000/api/:path*", // Proxy to Backend
      },
    ];
  },
};

export default nextConfig;
```

In the production environment, the interaction between the frontend and backend is handled differently to optimize performance and security. Instead of using the proxy setup defined in the development configuration, the frontend and backend services communicate through an Nginx server. The Nginx configuration, located in the frontend folder, acts as a reverse proxy, efficiently routing requests from the frontend to the backend.
