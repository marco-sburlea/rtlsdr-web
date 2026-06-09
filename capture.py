import os
import json
import uuid
import datetime
import threading
import logging
from config import Config
from device import run_command, format_frequency

logger = logging.getLogger(__name__)

capture_lock = threading.Lock()


def do_iq_capture(freq_hz, sample_rate, duration_sec, gain='auto', label=''):
    if not capture_lock.acquire(blocking=False):
        logger.warning("do_iq_capture: device busy, capture skipped")
        return False, {"error": "RTL-SDR busy", "success": False}
    try:
        ts = datetime.datetime.now().strftime(""%d-%m-%Y_%H-%M-%S"")
        uid = str(uuid.uuid4())[:8]
        filename = f"iq_{ts}_{uid}.iq"
        filepath = os.path.join(Config.CAPTURES_DIR, filename)

        num_samples = int(sample_rate * duration_sec)

        cmd = [
            Config.RTL_SDR_PATH,
            "-f", str(int(freq_hz)),
            "-s", str(int(sample_rate)),
            "-n", str(num_samples),
        ]
        if gain == 'auto':
            cmd += ["-A"]
        else:
            cmd += ["-g", str(int(float(gain) * 10))]
        cmd.append(filepath)

        logger.info(f"IQ capture: {' '.join(cmd)}")
        code, out, err = run_command(cmd, timeout=duration_sec + 10)

        success = code == 0 and os.path.exists(filepath)
        size = os.path.getsize(filepath) if success else 0

        meta = {
            "id": uid,
            "type": "iq",
            "filename": filename,
            "timestamp": ts,
            "frequency": freq_hz,
            "frequency_label": format_frequency(freq_hz),
            "sample_rate": sample_rate,
            "duration": duration_sec,
            "gain": gain,
            "label": label,
            "size_bytes": size,
            "success": success,
            "error": err if not success else ""
        }

        meta_path = filepath.replace('.iq', '.json')
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)

        return success, meta
    finally:
        capture_lock.release()


def do_sweep(start_hz, stop_hz, bin_size=1_000_000, gain='auto', label='', duration_sec=0):
    if not capture_lock.acquire(blocking=False):
        logger.warning("do_sweep: device busy, sweep skipped")
        return False, {"error": "RTL-SDR busy", "success": False}
    try:
        ts = datetime.datetime.now().strftime(""%d-%m-%Y_%H-%M-%S"")
        uid = str(uuid.uuid4())[:8]
        filename = f"sweep_{ts}_{uid}.csv"
        filepath = os.path.join(Config.CAPTURES_DIR, filename)

        cmd = [
            Config.RTL_POWER_PATH,
            "-f", f"{int(start_hz)}:{int(stop_hz)}:{int(bin_size)}",
            "-i", "1",
        ]
        if duration_sec > 0:
            cmd += ["-e", f"{int(duration_sec)}s"]
            timeout_val = int(duration_sec) + 20
        else:
            cmd += ["-1"]
            timeout_val = 30
        if gain != 'auto':
            cmd += ["-g", str(int(float(gain)))]
        cmd.append(filepath)

        logger.info(f"Sweep: {' '.join(cmd)}")
        code, out, err = run_command(cmd, timeout=timeout_val)

        success = code == 0 and os.path.exists(filepath)
        size = os.path.getsize(filepath) if success else 0

        meta = {
            "id": uid,
            "type": "sweep",
            "filename": filename,
            "timestamp": ts,
            "start_freq": start_hz,
            "stop_freq": stop_hz,
            "bin_size": bin_size,
            "gain": gain,
            "label": label,
            "duration_sec": duration_sec,
            "size_bytes": size,
            "success": success,
            "error": err if not success else ""
        }

        meta_path = filepath.replace('.csv', '.json')
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)

        return success, meta
    finally:
        capture_lock.release()


def parse_rtl_power_csv(filepath):
    points = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',')
                if len(parts) < 7:
                    continue
                try:
                    hz_low = float(parts[2])
                    hz_step = float(parts[4])
                    db_values = [float(x) for x in parts[6:] if x.strip()]
                    for i, db in enumerate(db_values):
                        freq = hz_low + (hz_step * i)
                        points.append({'freq_hz': freq, 'db': round(db, 2)})
                except (ValueError, IndexError):
                    continue
    except Exception as e:
        logger.error(f"CSV parse error: {e}")
    return points