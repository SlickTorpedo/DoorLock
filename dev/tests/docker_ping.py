import requests 

docker_ping_url = 'https://philipehrbright.tech/download/docker_ping'
docker_ping_url = 'http://localhost:5000/docker_ping'
hostname = input("Enter the hostname: ")
if hostname == "":
    hostname = "vl0igh-ip-150-135-165-16.philipehrbright.tech" #This is a test hostname, and may not always be available

try:
    hostname = hostname.split("://")[1]
except:
    pass

credentials = {
    'hostname': hostname,
}

def test(creds):
    r = requests.post(docker_ping_url, json=creds)
    if r.status_code == 200:
        print("Docker container is running!")
        return True
    elif r.status_code == 403:
        print("Docker container is not running!")
        return False
    elif r.status_code == 500:
        print("Server error. While this is not a success, it's not something we can fix, so we'll just keep going.")
        return True
    else:
        print("Something went wrong trying to find the tunnels.")
        print("Response: " + str(r.status_code))
        print("Response Text: " + str(r.text))
        return False
    
print(test(credentials))
print("Test completed")