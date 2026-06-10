import threading
import logging
from flask import Blueprint, request, jsonify
import scanner
from scanner import scan_band_continuous

logger = logging.getLogger(__name__)
bp = Blueprint('scan', __name__)


@bp.route('/api/scan/start', methods=['POST'])
def start_scan():
    if scanner.scan_active:
        return jsonify({"status": "already_running"})

    data = request.json
    start = float(data.get('start_freq', 87.5e6))
    stop = float(data.get('stop_freq', 108e6))
    bin_size = float(data.get('bin_size', 500_000))
    gain = data.get('gain', 'auto')
    threshold = float(data.get('threshold_db', -50))
    cap_duration = float(data.get('capture_duration', 5))
    cooldown = float(data.get('cooldown_sec', 30))

    from extensions import socketio
    scanner.scan_active = True
    thread = threading.Thread(
        target=scan_band_continuous,
        args=(start, stop, bin_size, gain, threshold, cap_duration, socketio, cooldown),
        daemon=True
    )
    thread.start()
    return jsonify({"status": "started"})


@bp.route('/api/scan/stop', methods=['POST'])
def stop_scan():
    scanner.scan_active = False
    return jsonify({"status": "stopped"})