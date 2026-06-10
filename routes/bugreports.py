import os
import re
import json
import datetime
import uuid
import logging
from flask import Blueprint, request, jsonify
from config import Config

logger = logging.getLogger(__name__)
bp = Blueprint('bugreports', __name__)


@bp.route('/api/bugreports/submit', methods=['POST'])
def submit_bugreport():
    data = request.json
    report_id = str(uuid.uuid4())[:8]
    now = datetime.datetime.now()
    ts_display = now.strftime("%d_%m_%Y_%H_%M_%S")
    ts_file = now.strftime("%d_%m_%Y_%H_%M_%S")

    report = {
        "id": report_id,
        "timestamp": ts_display,
        "name": data.get('name', 'Anonymous')[:100],
        "category": data.get('category', 'other'),
        "description": data.get('description', '')[:2000],
        "steps": data.get('steps', '')[:1000],
        "severity": data.get('severity', 'medium'),
        "status": "new"
    }

    filepath = os.path.join(
        Config.BUGREPORTS_DIR,
        f"report_{ts_file}_{report_id}.json"
    )
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Bug report received: {report_id} — {report['category']}")
    return jsonify({"status": "ok", "id": report_id})


@bp.route('/api/bugreports/list')
def list_bugreports():
    reports = []
    d = Config.BUGREPORTS_DIR
    for fn in sorted(os.listdir(d), reverse=True):
        if fn.endswith('.json'):
            try:
                with open(os.path.join(d, fn)) as f:
                    reports.append(json.load(f))
            except Exception as e:
                logger.warning(f"Corrupt bug report, skipped: {fn} — {e}")
    return jsonify(reports)


@bp.route('/api/bugreports/delete/<report_id>', methods=['DELETE'])
def delete_bugreport(report_id):
    if not re.match(r'^[a-f0-9]{8}$', report_id):
        return jsonify({"error": "Invalid id"}), 400

    d = Config.BUGREPORTS_DIR
    deleted = []
    for fn in os.listdir(d):
        if report_id in fn:
            os.remove(os.path.join(d, fn))
            deleted.append(fn)
    return jsonify({"deleted": deleted})