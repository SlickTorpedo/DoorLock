if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "This script is used to update the device manually. It will download the latest version of the firmware and install it on the device."
echo "Do you want to update the device? (y/n)"

read answer
if [ "$answer" != "${answer#[Yy]}" ] ;then
    echo "Updating the device..."
    #Download the latest version of the firmware
    git clone https://github.com/SlickTorpedo/DoorLock updated_software
    cp -r updated_software/* .
    rm -rf updated_software
    sudo systemctl restart webserver
    echo "Device updated successfully!"
else
    echo "Device not updated."
fi