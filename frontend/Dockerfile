# frontend/Dockerfile

# Stage 1: Build the React application
FROM node:20-alpine AS build

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install node modules
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Build the React app for production
# 'npm run build' typically outputs to a 'dist' (for Vite) or 'build' (for CRA) folder
RUN npm run build

# Stage 2: Serve the static files using Nginx
FROM nginx:stable-alpine

# Copy the built React app from the 'build' stage into Nginx's public directory
# If using Create React App, this path would be /app/build
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration (optional, but good for SPAs like React)
# This config ensures that all non-file requests are routed to index.html
# which is necessary for React Router to handle client-side routing.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 where Nginx will serve the frontend
EXPOSE 80

# Command to start Nginx (default for nginx:stable-alpine)
CMD ["nginx", "-g", "daemon off;"]