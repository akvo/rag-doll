FROM nginx:1.21.0-alpine

# Copy the build output to replace the default nginx contents.
COPY ./out /usr/share/nginx/html

# Copy the custom nginx configuration file.
COPY ./nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
