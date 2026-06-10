import logging
from flask import Blueprint, request, jsonify
from scheduler import add_job, remove_job, list_jobs

logger = logging.getLogger(__name__)
bp = Blueprint('schedule', __name__)


@bp.route('/api/schedule/add', methods=['POST'])
def add_schedule():
    data = request.json
    capture_type = data.get('capture_type', 'iq')
    cron_expr = data.get('cron', '0 * * * *')
    params = data.get('params', {})

    from app import socketio
    try:
        job_id, next_run = add_job(capture_type, cron_expr, params, socketio)
        return jsonify({"status": "added", "job_id": job_id, "next_run": next_run})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to add job: {e}")
        return jsonify({"error": str(e)}), 400


@bp.route('/api/schedule/remove/<job_id>', methods=['DELETE'])
def remove_schedule(job_id):
    try:
        remove_job(job_id)
        return jsonify({"status": "removed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route('/api/schedule/list')
def list_schedules():
    return jsonify(list_jobs())