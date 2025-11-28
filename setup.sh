#!/bin/bash
set -e  # Exit on error

K3S_SERVICE="k3s.service"
# Check if k3s service is deployed
if systemctl list-unit-files | grep -q "^$K3S_SERVICE"; then
    # Check if service is running
    if systemctl is-active --quiet "$K3S_SERVICE"; then
        echo "k3s is running"
    else
        echo "k3s is deployed but not running, starting the service..."
        sudo systemctl start "$K3S_SERVICE"
        # Verify start was successful
        if [ $? -eq 0 ]; then
            echo "Successfully started the k3s service"
        else
            echo "Failed to start k3s service" >&2
            exit 1
        fi
    fi
else
  echo "Installing k3s service...":
  curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--bind-address=0.0.0.0" sh -
  # Set necessary permission to k3s.yaml file
  echo "Setting read permission to k3s.yaml file"
  sudo chmod 644 /etc/rancher/k3s/k3s.yaml
fi

# Generate public/private rsa key pair
KEY_PATH="$HOME/.ssh"

if [ -f "$KEY_PATH/id_qstream" ] && [ -f "$KEY_PATH/id_qstream.pub" ]; then
  echo "ssh RSA key already exists at $KEY_PATH"
else
  echo "Generating SSH RSA key..."
  ssh-keygen -t rsa -b 4096 -f "$KEY_PATH/id_qstream" -N ""
  echo "ssh RSA key generated at $KEY_PATH"
fi

if [ -n "$VIRTUAL_ENV" ]; then
    venv_path=$VIRTUAL_ENV
else
  # Find a valid Python interpreter
  python_exe=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
  if [ -z "$python_exe" ]; then
      echo "Python not found." >&2
      exit 1
  fi

  # Use Python to detect venv and get path
  venv_path=$("$python_exe" -c "import sys; print(sys.prefix if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix else '')")
fi

if [ ! -n "$venv_path" ]; then
    echo "Python virtual environment is not found!. Please activate the virtual environment using the below command and then run this script."
    echo "source <venv_path>/bin/activate"
    exit 1
fi

echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Packages installed successfully."

echo "Deploying the quarkifi-stream-k3s-client service..."

# configure the quarkifi-stream-k3s-client.service.service file
cwd=$(pwd)
user=$(whoami)

service_file="$cwd/quarkifi-stream-k3s-client.service"
sed -i "s|{{USER}}|$user|g" "$service_file"
sed -i "s|{{CWD}}|$cwd|g" "$service_file"
sed -i "s|{{VENV_PATH}}|$venv_path|g" "$service_file"
sudo cp $service_file /etc/systemd/system/.
sudo systemctl daemon-reload
sudo systemctl enable quarkifi-stream-k3s-client

echo "Deploying the quarkifi-stream-ssh-tunnel service..."
service_file="$cwd/quarkifi-stream-ssh-tunnel.service"
sed -i "s|{{USER}}|$user|g" "$service_file"
sudo cp $service_file /etc/systemd/system/.
sudo systemctl daemon-reload
sudo systemctl enable quarkifi-stream-ssh-tunnel
