# Use an official Node.js image as the base image
FROM node:16

# Create a directory to hold the application code
RUN mkdir -p /usr/src/app

# Copy the package.json and package-lock.json files
COPY package*.json /usr/src/app/

# Set the working directory
WORKDIR /usr/src/app

# Install the application's dependencies
RUN npm install

# Copy the rest of the application code
COPY . /usr/src/app

# Expose the port that the application will run on
EXPOSE 3000

# Start the application
CMD ["node", "index.js"]
