# Walkthrough - Plex Status Display

This guide explains how to set up and run your real-time Plex and system status monitor.

## Hardware Setup

1.  **Arduino & LCD**: Connect your 16x4 I2C LCD to your Arduino:
    -   **GND** -> GND
    -   **VCC** -> 5V
    -   **SDA** -> A4 (Uno/Nano) or dedicated SDA
    -   **SCL** -> A5 (Uno/Nano) or dedicated SCL
2.  **USB**: Connect the Arduino to your host computer via USB.
3.  **Flash Sketch**: Use the Arduino IDE to upload [plex_display.ino](file:///c:/Users/Roberto/Documents/Antigravity/plexScreen/plex_display/plex_display.ino) to your board.
    - *Note: This sketch is configured for a **20x4 LCD**, **115200 baud**, and **Button on D2**.*
    - *Ensure you have the `LiquidCrystal_I2C` library installed.*
4.  **Hardware Button**: Connect a momentary push-button between **Pin D2** and **GND**. When pressed, it will cycle through the different views.

## Authentication & Setup

If your Plex token is invalid or expires, the system will enter **Setup Mode**:
1.  The LCD will display an authentication failure message and a **Setup URL** (e.g., `http://192.168.1.13:5000`).
2.  Open this URL in any browser on your network.
3.  Enter your new Plex Token in the web form and click **Save**.
4.  The script will automatically update your `.env` file and resume the monitoring loop.

1.  **Python Environment**: I have already set up a virtual environment and installed the dependencies in [c:/Users/Roberto/Documents/Antigravity/plexScreen](file:///c:/Users/Roberto/Documents/Antigravity/plexScreen).
2.  **Environment Variables**:
    -   Locate the [.env](file:///c:/Users/Roberto/Documents/Antigravity/plexScreen/.env) file in the project directory.
    -   Update `PLEX_TOKEN` with your Plex token. (Find it [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)).
    -   Update `SERIAL_PORT` if your Arduino is not on `COM3`.
-   Update `LCD_BRIGHTNESS` (0 to 255). 
    - *Note: Without hardware mods, 0 is OFF and 1-255 is ON.*

## Brightness Control (Advanced)

By default, the script can turn the backlight ON or OFF. To enable **true dimming** (0-100%):
1. Remove the **jumper** on the back of the I2C backpack.
2. Connect the pin closest to the edge (usually labeled LED) to Arduino **Pin D9**.
3. In [plex_display.ino](file:///c:/Users/Roberto/Documents/Antigravity/plexScreen/plex_display/plex_display.ino), uncomment these lines in `setup()`:
   ```cpp
   pinMode(BACKLIGHT_PIN, OUTPUT); 
   usePWM = true;
   ```

To start the monitor, run the following command in your terminal:

```powershell
# From the project directory
.\venv\Scripts\activate
python plex_monitor.py
```

## How it Works

- **Row 1**: Displays "P: [Movie/Show Title]" (truncated to fit).
- **Row 2**: Displays "U: [Username]" of the person currently watching.
- **Row 3**: Displays CPU and RAM usage percentage.
- **Row 4**: Displays GPU usage percentage (if NVIDIA GPU is detected).

### Customization
- You can adjust the `UPDATE_INTERVAL` in [plex_monitor.py](file:///c:/Users/Roberto/Documents/Antigravity/plexScreen/plex_monitor.py) to change how often the screen refreshes.
- If your LCD has a different I2C address, update it in [plex_display.ino](file:///c:/Users/Roberto/Documents/Antigravity/plexScreen/plex_display.ino) (default is `0x27`).
