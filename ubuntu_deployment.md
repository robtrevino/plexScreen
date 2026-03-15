# Ubuntu Deployment Guide: Plex Monitor

Follow these steps to deploy and run your Plex Monitor on an Ubuntu server.

## 1. Prerequisites

Ensure your system is up to date and has the necessary Python tools:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip -y
```

## 2. Hardware Permissions

On Linux, serial ports are usually restricted. Add your user to the `dialout` group so the script can access the Arduino:

```bash
sudo usermod -a -G dialout $USER
```
*Note: You may need to log out and back in for this to take effect.*

## 3. Project Setup

1.  **Copy Files**: Transfer the project folder to your server (e.g., using `scp` or `git`).
2.  **Create Virtual Environment**:
    ```bash
    cd /path/to/plexScreen
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools  # Fixes 'distutils' error in Python 3.12+
    pip install -r requirements.txt
    ```

## 4. Configuration (.env)

Edit your [.env](file:///c:/Users/Roberto/Documents/Antigravity/plexScreen/.env) file to match the Linux environment:

1.  **Identify Serial Port**: Plug in your Arduino and run `ls /dev/tty*`. It is usually `/dev/ttyUSB0` or `/dev/ttyACM0`.
2.  **Update .env**:
    ```ini
    PLEX_URL=http://localhost:32400
    PLEX_TOKEN=your_plex_token
    SERIAL_PORT=/dev/ttyACM0  # <--- Update this to your Linux port!
    LCD_BRIGHTNESS=255
    ```

## 5. Persistence (Run as a Service)

To ensure the monitor starts automatically and stays running, create a systemd service:

1.  **Create Service File**:
    ```bash
    sudo nano /etc/systemd/system/plex-monitor.service
    ```
2.  **Paste the Following** (replace `/path/to/plexScreen` and `youruser` with your actual path and username):
    ```ini
    [Unit]
    Description=Plex LCD Monitor Service
    After=network.target

    [Service]
    Type=simple
    User=youruser
    WorkingDirectory=/path/to/plexScreen
    ExecStart=/path/to/plexScreen/venv/bin/python plex_monitor.py
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target
    ```
3.  **Enable and Start**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable plex-monitor
    sudo systemctl start plex-monitor
    ```

## 6. Troubleshooting

- **Check Logs**: `sudo journalctl -u plex-monitor -f`
- **Serial Issues**: Run `ls -l /dev/ttyACM0` to verify ownership and permissions.
