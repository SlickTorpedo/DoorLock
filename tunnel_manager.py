from registrar_server import RegistrarClient

import requests
import os
from tqdm import tqdm
import json

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
        response = requests.post(self.download_url, json=self.credentials, stream=True)
        
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

    def installAndRunDocker(self, error_code=0):
        if not os.path.exists(self.file_path):
            print('ERROR: File not found')
            return
        
        if error_code == 0:
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
                    print('Tunnel URL pushed to registrar')
                else:
                    print('ERROR: Something went wrong during the execution of the container')
            except Exception as e:
                print('ERROR: Could not parse the output ', str(e))
            return output
        
        if error_code == 1:
            print('ERROR: Something went wrong during the download, please try again')
            return False

        if error_code == 2:
            print('No download needed, running the container...')
            os.system(f'sudo chmod +x {self.file_path}')
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
                    print('Tunnel URL pushed to registrar')
                else:
                    print('ERROR: Something went wrong during the execution of the container')
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
    tunnel_downloader = TunnelDownloader()
    tunnel_downloader.installAndRunDocker(tunnel_downloader.download())
