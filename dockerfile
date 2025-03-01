# Use a base image with Node.js
FROM node:20-bullseye

# Install Python and pip
RUN apt update && apt install -y python3 python3-pip

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json separately for better caching
COPY package.json package-lock.json ./

# Install Node.js dependencies
RUN npm install

# Copy all project files into the container
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Expose the necessary port
EXPOSE 3000

# Start the application
CMD ["node", "app.js"]
