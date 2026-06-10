import os
import re
import json
import logging
from flask import Blueprint, jsonify, send_from_directory
from config import Config

logger = logging.getLogger(__name__)
bp = Blueprint('captures', __name__)


@bp.route('/api/captures/list')
def list_captures():
    captures = []
    cap_dir = Config.CAPTURES_DIR
    for fn in sorted(os.listdir(cap_dir), reverse=True):
        if fn.endswith('.json'):
            try:
                with open(os.path.join(cap_dir, fn)) as f:
                    captures.append(json.load(f))
            except Exception as e:
                logger.warning(f"Corrupt metadata file, skipped: {fn} — {e}")
    return jsonify(captures[:100])


@bp.route('/api/captures/download/<filename>')
def download_capture(filename):
    return send_from_directory(Config.CAPTURES_DIR, filename, as_attachment=True)


@bp.route('/api/captures/delete/<uid>', methods=['DELETE'])
def delete_capture(uid):
    if not re.match(r'^[a-f0-9]{8}$', uid):
        return jsonify({"error": "Invalid id"}), 400

    cap_dir = Config.CAPTURES_DIR
    deleted = []
    for fn in os.listdir(cap_dir):
        if uid in fn:
            os.remove(os.path.join(cap_dir, fn))
            deleted.append(fn)
    return jsonify({"deleted": deleted})