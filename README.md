# RTL-SDR Web Interface

A web-based control panel for RTL-SDR devices, built with Flask and SocketIO.

## Features

- **IQ Capture** — record raw IQ samples at any frequency
- **Frequency Sweep** — scan a frequency range with rtl_power
- **Band Scan** — continuous spectrum monitoring with automatic threshold-triggered captures
- **Scheduler** — cron-based scheduled captures
- **Captures Manager** — browse, download and delete saved captures
- **Bug Reports** — built-in feedback form

## Hardware Requirements

- RTL-SDR dongle (RTL2832U chipset)
- Linux system (tested on Ubuntu 20.04/22.04, Raspberry Pi OS)

## Installation

```bash
git clone https://github.com/marco-sburlea/rtlsdr-web.git
cd rtlsdr-web
chmod +x install.sh
./install.sh
```

## Project Structure

```
rtlsdr-web/
├── app.py          # Flask app init, blueprints, socketio
├── config.py       # paths and constants
├── device.py       # RTL-SDR detection, command runner
├── capture.py      # IQ capture and frequency sweep logic
├── scanner.py      # continuous band scan with threshold trigger
├── scheduler.py    # APScheduler cron job management
├── sockets.py      # SocketIO event handlers
├── routes/         # Flask blueprints (one per feature)
├── templates/      # HTML frontend
└── captures/       # saved IQ and sweep files
```

## Roadmap

- [ ] Docker support
- [ ] Pluto SDR support
- [ ] FOBOS SDR support
- [ ] IQ file analysis tools using ML
- [ ] Dynamic threshold — adaptive noise floor using Z-score / CFAR
- [ ] Baseline calibration — detect phase deviations
- [ ] Anomaly detection — statistical models for signal classification
- [ ] Alert system — email notifications on threshold trigger
- [ ] Multi-device support — switch between SDR devices via web UI
- [ ] Recording scheduler improvements — GPS timestamp, location tagging

## License

MIT License — feel free to use, modify and distribute.