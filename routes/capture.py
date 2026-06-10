import threading
import logging
from flask import Blueprint, request, jsonify
from capture import do_iq_capture, do_sweep
from config import Config

logger = logging.getLogger(__name__)
bp = Blueprint('capture', __name__)


def validate_gain(gain):
    if gain == 'auto':
        return gain, None
    try:
        g = float(gain)
        if not (Config.GAIN_MIN <= g <= Config.GAIN_MAX):
            raise ValueError
        return g, None
    except (ValueError, TypeError):
        return None, "Invalid gain value"


@bp.route('/api/capture/iq', methods=['POST'])
def capture_iq():
    from app import socketio as sio
    data = request.json
    freq = float(data.get('frequency', 100e6))
    rate = float(data.get('sample_rate', 2_048_000))
    duration = float(data.get('duration', 5))
    label = data.get('label', '')
    gain, err = validate_gain(data.get('gain', 'auto'))
    if err:
        return jsonify({"error": err}), 400

    def run():
        sio.emit('capture_started', {'type': 'iq'}, namespace='/')
        success, meta = do_iq_capture(freq, rate, duration, gain, label)
        sio.emit('capture_done', meta, namespace='/')

    sio.start_background_task(run)
    return jsonify({"status": "started"})


@bp.route('/api/capture/sweep', methods=['POST'])
def capture_sweep():
    from app import socketio as sio
    data = request.json
    start = float(data.get('start_freq', 87.5e6))
    stop = float(data.get('stop_freq', 108e6))
    bin_size = float(data.get('bin_size', 1e6))
    duration_sec = float(data.get('duration_sec', 0))
    label = data.get('label', '')
    gain, err = validate_gain(data.get('gain', 'auto'))
    if err:
        return jsonify({"error": err}), 400

    def run():
        sio.emit('capture_started', {'type': 'sweep'}, namespace='/')
        success, meta = do_sweep(start, stop, bin_size, gain, label, duration_sec)
        sio.emit('capture_done', meta, namespace='/')

    sio.start_background_task(run)
    return jsonify({"status": "started"})