import os
import time
import shutil
import logging
from flask import Blueprint, jsonify
from config import Config

logger = logging.getLogger(__name__)
bp = Blueprint('system', __name__)


@bp.route('/api/device/status')
def device_status():
    from device import check_rtlsdr
    ok, msg = check_rtlsdr()
    return jsonify({"connected": ok, "message": msg})


@bp.route('/api/disk/usage')
def disk_usage():
    cap_dir = Config.CAPTURES_DIR
    total, used, free = shutil.disk_usage('/')
    cap_size = sum(
        os.path.getsize(os.path.join(cap_dir, f))
        for f in os.listdir(cap_dir)
        if os.path.isfile(os.path.join(cap_dir, f))
    )
    return jsonify({
        'total': total,
        'used': used,
        'free': free,
        'captures_size': cap_size,
        'percent_used': round(used / total * 100, 1)
    })


@bp.route('/api/system/stats')
def system_stats():
    with open('/proc/stat') as f:
        cpu_line = f.readline().split()
    idle1 = int(cpu_line[4])
    total1 = sum(int(x) for x in cpu_line[1:])

    time.sleep(0.5)

    with open('/proc/stat') as f:
        cpu_line = f.readline().split()
    idle2 = int(cpu_line[4])
    total2 = sum(int(x) for x in cpu_line[1:])

    cpu_pct = round((1 - (idle2 - idle1) / (total2 - total1)) * 100, 1)

    mem = {}
    with open('/proc/meminfo') as f:
        for line in f:
            parts = line.split()
            mem[parts[0].rstrip(':')] = int(parts[1]) * 1024

    ram_total = mem['MemTotal']
    ram_free = mem['MemAvailable']
    ram_used = ram_total - ram_free
    ram_pct = round(ram_used / ram_total * 100, 1)

    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            temp = round(float(f.read()) / 1000, 1)
    except Exception:
        temp = None

    return jsonify({
        'cpu_pct': cpu_pct,
        'ram_total': ram_total,
        'ram_used': ram_used,
        'ram_free': ram_free,
        'ram_pct': ram_pct,
        'cpu_temp': temp
    })