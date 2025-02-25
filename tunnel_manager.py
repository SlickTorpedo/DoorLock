from registrar_server import RegistrarClient

import requests
import os
from tqdm import tqdm
import json

registrar_client = RegistrarClient()

class Tunnel:
    def __init__(self):
        self.download_url = 'https://philipehrbright.tech/download/'
        self.docker_ping_url = 'https://philipehrbright.tech/download/docker_ping'
        self.credentials = {
            'serial': registrar_client.get_serial_number(),
            'secret': registrar_client.get_secret()
        }
        self.cf_tunnel_url = 'https://doorlock-cf-' + self.credentials['serial'] + '.philipehrbright.tech/'
        self.file_path = 'docker_container.tar'
        self.container_script_path = 'run_container.sh'
        self.tunnel_url = None

    def get_tunnel_url(self):
        if self.tunnel_url is None:
            return self.cf_tunnel_url
        return self.tunnel_url

    def download(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

        try:
            response = requests.post(self.download_url, json=self.credentials, stream=True)
        except requests.exceptions.RequestException as e:
            print(f'ERROR WITH DOCKER DOWNLOAD: {e}')
            print("This isn't a huge issue as long as there's no update to the tunnel software (which there never is).")
            return 4
        
        if response.status_code == 200:
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 Kibibyte
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
            
            print("Starting download...")
            with open(self.file_path, 'wb') as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
            progress_bar.close()

            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                print("ERROR: Something went wrong during the download")
                return 1

            print('File downloaded successfully')
            return 0

        elif response.status_code == 403:
            print('No download needed!')
            return 2
        elif response.status_code == 401 or response.status_code == 400:
            print('Unauthorized (your serial or secret is wrong)')
            return 3
        else:
            print(f'Unexpected error: {response.status_code}')
            print(f'Response: {response.text}')
            return 4

    def send_docker_ping(self):
        creds = {
            'hostname': self.tunnel_url.split("://")[1]
        }
        print("Sending Docker Ping to " + self.docker_ping_url)
        try:
            r = requests.post(self.docker_ping_url, json=creds)
        except requests.exceptions.RequestException as e:
            print(f'ERROR WITH DOCKER PING: {e}')
            print("This is okay, the device automatically falls back to a CF Tunnel!")
            return False
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

    def docker_container_status(self):
        #Check if it's using a CF tunnel, if so, return True
        if self.tunnel_url == self.cf_tunnel_url:
            return True #It's using a CF tunnel so it's fine, it will check again in 5 minutes
        res = os.popen('sudo docker ps -q | wc -l').read().strip()
        try:
            if(int(res) < 1):
                print("No active tunnels!")
                return False
            else:
                return self.send_docker_ping()
        except Exception as e:
            print("Something went wrong trying to find the tunnels.")
            print("Command Result: " + str(res))
            print("Error: " + str(e))
            return False

    def installAndRunDocker(self, error_code=2):
        if error_code == 0:
            if not os.path.exists(self.file_path):
                print('ERROR: File not found')
                return False

            os.system(f'sudo chmod +x {self.file_path}')
            os.system(f'sudo chmod +x {self.container_script_path}')
            output = os.popen(f'bash ./{self.container_script_path} {self.file_path}').read()
            print("Script output: ", output)
            for x in range(3):
                print(" ")
            try:
                output = json.loads(output)
                if output['success'] == 'true':
                    print('Tunnel URL:', output['tunnel_url'])
                    print('Container ID:', output['container_id'])
                    print(registrar_client.push_tunnel(output['tunnel_url']))
                    self.tunnel_url = output['tunnel_url']
                    print('Tunnel URL pushed to registrar')
                else:
                    print('ERROR: Something went wrong during the execution of the container')
                    print("This isn't the best, but it's not the end of the world. The device will try again in 5 minutes.")
                    print("In the meantime it will use a Cloudflare tunnel as a backup.")
                    # Post the Tunnel URL instead which is self.cf_tunnel_url
                    print("RESULT FROM CF TUNNEL PUSH (1): ", registrar_client.push_tunnel(self.cf_tunnel_url))
                    self.tunnel_url = self.cf_tunnel_url
                    print("Tunnel URL pushed to registrar [CF TUNNEL]")
            except Exception as e:
                print('ERROR: Could not parse the output ', str(e))
            return output
        
        if error_code == 1:
            print('ERROR: Something went wrong during the download, please try again')
            return False

        if error_code == 2:
            print('No download needed, running the container...')
            os.system(f'sudo chmod +x {self.container_script_path}')
            output = os.popen(f'bash ./{self.container_script_path}').read()
            print("Script output: ", output)
            for x in range(3):
                print(" ")
            try:
                output = json.loads(output)
                if output['success'] == 'true':
                    print('Tunnel URL:', output['tunnel_url'])
                    print('Container ID:', output['container_id'])
                    print(registrar_client.push_tunnel(output['tunnel_url']))
                    self.tunnel_url = output['tunnel_url']
                    print('Tunnel URL pushed to registrar')
                else:
                    print('ERROR: Something went wrong during the execution of the container')
                    print("This isn't the best, but it's not the end of the world. The device will try again in 5 minutes.")
                    print("In the meantime it will use a Cloudflare tunnel as a backup.")
                    # Post the Tunnel URL instead which is self.cf_tunnel_url
                    print("RESULT FROM CF TUNNEL PUSH (2): " + registrar_client.push_tunnel(self.cf_tunnel_url))
                    self.tunnel_url = self.cf_tunnel_url
                    print("Tunnel URL pushed to registrar [CF TUNNEL]")
            except Exception as e:
                print('ERROR: Could not parse the output ', str(e))
            return output
    
        if error_code == 3:
            print('Unauthorized (your serial or secret is wrong)')
            return False
        
        if error_code == 4:
            print('Unexpected error')
            return False

if __name__ == '__main__':
    tunnel_downloader = Tunnel()
    tunnel_downloader.installAndRunDocker(tunnel_downloader.download())
