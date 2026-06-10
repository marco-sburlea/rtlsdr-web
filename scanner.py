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


def auto_capture_on_threshold(freq_hz, duration, gain, socketio):
    success, meta = do_iq_capture(freq_hz, Config.DEFAULT_SAMPLE_RATE, duration, gain, label='auto_threshold')
    socketio.emit('auto_capture_done', meta)


def scan_band_continuous(start_hz, stop_hz, bin_size, gain, threshold_db, capture_duration, socketio, cooldown_sec=30):
    global scan_active, last_trigger_time
    logger.info(f"Band scan started: {start_hz}-{stop_hz} Hz, threshold={threshold_db} dB")

    while scan_active:
        if not capture_lock.acquire(blocking=False):
            logger.info("Scan delayed: device busy with IQ capture")
            time.sleep(1)
            continue

        tmp_file = f"/tmp/rtlsdr_scan_{int(time.time())}.csv"

        cmd = [
            Config.RTL_POWER_PATH,
            "-f", f"{int(start_hz)}:{int(stop_hz)}:{int(bin_size)}",
            "-i", "1", "-1",
        ]
        if gain != 'auto':
            cmd += ["-g", str(int(float(gain)))]
        cmd.append(tmp_file)

        try:
            code, out, err = run_command(cmd, timeout=15)
        finally:
            capture_lock.release()

        if not scan_active:
            try:
                os.remove(tmp_file)
            except Exception:
                pass
            break

        if code == 0 and os.path.exists(tmp_file):
            data_points = parse_rtl_power_csv(tmp_file)

            if data_points:
                socketio.emit('scan_data', {'points': data_points})

                with trigger_lock:
                    in_cooldown = (time.time() - last_trigger_time) < cooldown_sec

                if in_cooldown:
                    remaining = int(cooldown_sec - (time.time() - last_trigger_time))
                    socketio.emit('scan_cooldown', {'remaining': remaining, 'total': cooldown_sec})

                for pt in data_points:
                    if pt['db'] >= threshold_db:
                        logger.info(f"Threshold exceeded at {pt['freq_hz']} Hz: {pt['db']} dB")

                        if in_cooldown:
                            remaining = int(cooldown_sec - (time.time() - last_trigger_time))
                            socketio.emit('threshold_triggered', {
                                'freq': pt['freq_hz'],
                                'freq_label': format_frequency(pt['freq_hz']),
                                'db': pt['db'],
                                'threshold': threshold_db,
                                'ignored': True,
                                'cooldown_remaining': remaining
                            })
                        else:
                            with trigger_lock:
                                last_trigger_time = time.time()
                            socketio.emit('threshold_triggered', {
                                'freq': pt['freq_hz'],
                                'freq_label': format_frequency(pt['freq_hz']),
                                'db': pt['db'],
                                'threshold': threshold_db,
                                'ignored': False,
                                'cooldown_remaining': 0
                            })
                            threading.Thread(
                                target=auto_capture_on_threshold,
                                args=(pt['freq_hz'], capture_duration, gain, socketio),
                                daemon=True
                            ).start()
                            time.sleep(0.1)
                        
                        break

            try:
                os.remove(tmp_file)
            except Exception:
                pass
        else:
            socketio.emit('scan_error', {'message': f"rtl_power error: {err[:200]}"})
            time.sleep(2)

    socketio.emit('scan_stopped', {})
    logger.info("Band scan stopped")