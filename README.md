# Plex Status Monitor (plexScreen)

A real-time monitoring system for your Plex Media Server and host system metrics, displayed on an Arduino-driven 20x4 LCD.

## Overview

The Plex Status Monitor is a Python-based utility that fetches active session data from your Plex server and combines it with local system performance metrics (CPU, RAM, GPU, and Disk). This data is then streamed over serial to an Arduino, which displays it on a 20x4 I2C LCD.

## Key Features

- **Real-Time Plex Monitoring**: Displays the title of the media being played and the username of the viewer.
- **System Metrics**: Monitors CPU, RAM, and GPU usage, along with disk storage levels.
- **Multiple Views**: Cycle through different information screens using a physical hardware button.
  - **Main View**: Plex status + CPU/RAM/GPU usage.
  - **Disk View**: Visual bars for all connected storage drives.
  - **Stream Detail**: Detailed progress bars and resolution info for active streams.
- **Easy Setup**: Includes a built-in web server for easy Plex token configuration if authentication fails.
- **Ubuntu Ready**: Optimized for deployment as a background service on Linux servers.

## Documentation

For detailed instructions, please refer to the following guides:

- **[Setup & Walkthrough](walkthrough.md)**: Hardware wiring, environment configuration, and basic usage.
- **[Ubuntu Deployment Guide](ubuntu_deployment.md)**: Steps for setting permissions and running the monitor as a `systemd` service on Linux.

## Hardware Requirements

- Arduino (Uno, Nano, or similar)
- 20x4 I2C LCD Display
- Momentary push-button (for view cycling)
- (Optional) Jumper wire for PWM brightness control

## Quick Start (Local)

1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your `PLEX_TOKEN` and `SERIAL_PORT`.
4. Upload `plex_display.ino` to your Arduino.
5. Run the monitor: `python plex_monitor.py`
