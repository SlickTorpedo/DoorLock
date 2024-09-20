#!/bin/bash

#This file will run the Docker container and extract the tunnel URL from the logs.

# Function to install Docker if not found
install_docker() {
    echo "Docker not found. Installing Docker..."

    # Update the package database
    sudo apt-get update -qq >/dev/null

    # Install Docker prerequisites
    sudo apt-get install -qq -y apt-transport-https ca-certificates curl software-properties-common >/dev/null 2>&1

    # Add Docker’s official GPG key
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg >/dev/null 2>&1

    # Add Docker’s stable repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

    # Update the package database again with Docker's repo
    sudo apt-get update -qq >/dev/null

    # Install Docker
    sudo apt-get install -qq -y docker-ce docker-ce-cli containerd.io >/dev/null 2>&1

    # Verify Docker installation
    if ! command -v docker &> /dev/null
    then
        echo "{\"tunnel_url\":\"\",\"container_id\":\"\",\"success\":\"false\", \"error\":\"Docker installation failed\"}"
        exit 1
    fi
}

# Check if Docker is installed, if not, install it
if ! command -v docker &> /dev/null
then
    install_docker
fi

# If an argument (file path) is provided, perform docker load, otherwise skip to running the container
if [ -n "$1" ]
then
    # Store the file path argument
    file_path=$1

    # Check if the file exists
    if [ ! -f "$file_path" ]
    then
        echo "{\"tunnel_url\":\"\",\"container_id\":\"\",\"success\":\"false\", \"error\":\"File not found: $file_path\"}"
        exit 1
    fi

    # Import the extracted tar file as a Docker image, suppressing output
    if ! sudo docker load -i "$file_path" >/dev/null 2>&1; then
        echo "{\"tunnel_url\":\"\",\"container_id\":\"\",\"success\":\"false\", \"error\":\"Failed to load Docker image\"}"
        rm "$temp_file" >/dev/null 2>&1
        exit 1
    fi

    # Clean up the temporary file, suppressing output
    rm "$temp_file" >/dev/null 2>&1
fi

# Run the Docker image (tunnel-service) and capture the container ID, suppressing output
container_id=$(sudo docker run --label app=tunnelmole --rm -d --network host tunnel-service 2>/dev/null)

if [ -z "$container_id" ]; then
    echo "{\"tunnel_url\":\"\",\"container_id\":\"\",\"success\":\"false\", \"error\":\"Failed to start Docker container\"}"
    exit 1
fi

# Monitor the logs and extract the tunnel URL
tunnel_url=""
end=$((SECONDS+20))  # Set the timeout to 20 seconds

# Use a loop to continuously check the logs for the URL until timeout
while [ $SECONDS -lt $end ]; do
    log_output=$(sudo docker logs "$container_id" 2>/dev/null)

    # Check if the tunnel URL is found
    tunnel_url=$(echo "$log_output" | grep -Eo "https://[a-zA-Z0-9.-]+\.philipehrbright\.tech")

    if [ ! -z "$tunnel_url" ]; then
        break  # Exit loop if tunnel URL is found
    fi

    sleep 1  # Wait 1 second before checking again
done

# Capture the exit code and generate the final JSON object
if [ -z "$tunnel_url" ]; then
    echo "{\"tunnel_url\":\"\",\"container_id\":\"$container_id\",\"success\":\"false\", \"error\":\"Failed to retrieve tunnel URL from logs\"}"
else
    echo "{\"tunnel_url\":\"$tunnel_url\",\"container_id\":\"$container_id\",\"success\":\"true\"}"
fi