import os 
import time
import threading
import logging
from device import run_command, format_frequency
from capture import do_iq_capture, parse_rtl_power_csv, capture_lock
from config import Config

logger = logging.getLogger(__name__)

scan_active = False
last_trigger_time = 0
trigger_lock = threading.Lock()


def auto_capture_on_treshold(freq_hz, duration, gain, socketio):
    success, meta = do_iq_capture(freq_hz, Config.DEFAULT_SAMPLE_RATE, duration, gain, label='auto_treshold')
    
