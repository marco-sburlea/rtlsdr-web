import subprocess   
import logging
from config import Config

logger = logging.getLogger(__name__)

def check_rtlsdr():
    try:
        result = subprocess.run(
            [Config.LSUSB_PATH],
            shell=False,
            capture_output=True,
            text=True,
            timeout=3
        )
        if "0bda" in result.stdout.lower:
            return True, "RTL-SDR Online"
    except Exception as e:
        logger.error(f"check_rtlsdr error: {e}")
    return False, "Device not detected"


def run_command(cmd, timeout=60):
    try:
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "","Command timed out"
    except Exception as e:
        return -1, "", str(e)


def format_frequency(freq_hz):
    if freq_hz >= 1e9:
        return f"{freq_hz/1e9:.3f} GHz"
    elif freq_hz >= 1e6:
        return f"{freq_hz/1e6:.3f} MHz"
    elif freq_hz >= 1e3:
        return f"{freq_hz/1e3:.3f} kHz"
    return f"{freq_hz:.0f} Hz"