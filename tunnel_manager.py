from registrar_server import RegistrarClient
import requests
import os

registrar_client = RegistrarClient()

class TunnelDownloader:
    def __init__(self):
        self.download_url = 'https://philipehrbright.tech/download'
        self.credentials = {
            'serial': registrar_client.get_serial_number(),
            'secret': registrar_client.get_secret()
        }
        self.file_path = 'docker_container.tar'
        self.container_script_path = 'run_container.sh'

    def download(self):
        response = requests.post(self.download_url, json=self.credentials)
        if response.status_code == 200:
            with open(self.file_path, 'wb') as file:
                file.write(response.content)
            print('File downloaded successfully')
            return True
        elif response.status_code == 403:
            print('No download needed!')
            return True
        elif response.status_code == 401 or response.status_code == 400:
            print('unauthorized')
            return False
        else:
            print(f'Unexpected error: {response.status_code}')
            return False
        
    def installAndRunDocker(self):
        os.system(f'chmod +x {self.file_path}')
        os.system(f'chmod +x {self.container_script_path}')
        output = os.popen(f'bash ./{self.container_script_path}').read()
        print("Script output: ", output)
        return output

if __name__ == '__main__':
    tunnel_downloader = TunnelDownloader()
    if tunnel_downloader.download():
        tunnel_downloader.installAndRunDocker()