# Use a base image with Node.js and Python
FROM node:20-bullseye

# Install Python and pip
RUN apt update && apt install -y python3 python3-pip

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and install Node.js dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the project files
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Expose the necessary port
EXPOSE 3000

# Start the application
CMD ["node", "app.js"]
