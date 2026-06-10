import re
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


@bp.route('/api/capture/iq', methods = ['POST'])
def capture_iq():
    data = request.json
    freq = float(data.get('frequency', 100e6))
    rate = float(data.get('samples rate', 2_048_000))
    duration = float(data.get('duration', 5))
    label = data.get('label', '')
    gain, err = validate_fain(data.get('gain', 'auto'))
    if err:
        return jsonify({"error": err}), 400

    from app import socketio
    def run():
        socketio.emit('capture_started', {'type': 'iq'})
        succes, meta = do_iq_capture(freq, rate, duration, gain, label)
        socketio.emit('capture_done', meta)

    threadi