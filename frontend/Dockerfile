# Use the official Node.js LTS (Long Term Support) image
FROM node:18-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install project dependencies
RUN npm install

# Expose the development server port (default is 5173 for Vite)
EXPOSE 5173

# Command to start the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]