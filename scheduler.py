import datetime
import logging
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduled_jobs = {}


def init_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

def add_job(capture_type, cron_expr, params, socketio):
    job_id = str(uuid.uuid4())[:8]

    def scheduled_task():
        logger.info(f"Scheduled task {job_id} running")
        from capture import do_iq_capture, do_sweep
        if capture_type == 'iq':
            success, meta = do_iq_capture(
                params.get('frequency',100e6),
                params.get('sample_rate',2_048_000),
                params.get('duration', 5),
                params.get('gain', 'auto'),
                label = f'scheduled_{job_id}'

            )
        else:
            success, meta = do_sweep(
                params.get('start_freq', 87.5e6),
                params.get('stop_freq', 108e6),
                params.get('bin_size', 1e6),
                params.get('gain','auto'),
                label = f'scheduled_{job_id}'
            )
        socketio.emit('scheduled_capture_done',{'job_id':job_id, 'meta':meta})

    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError("Invalid cron expression - need exactly 5 fields")

    trigger = CronTrigger(
        minute = parts[0], 
        hour = parts[1],
        day = parts[2],
        month = parts[3],
        day_of_week = parts[4] 
    )

    job = scheduler.add_job(scheduled_task, trigger, id=job_id)
    scheduled_jobs[job_id] = {
        "id": job_id,
        "cron": cron_expr,
        "capture_type": capture_type,
        "params": params,
        "created": datetime.datetime.now().isoformat(),
        "next_run": str(job.next_run_time)
    }
    return job_id, str(job.next_run_time)


def remove_job(job_id):
    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        logger.warning(f"Job {job_id} not found in scheduler")
    scheduled_jobs.pop(job_id, None)

def list_jobs():
    result = []
    for jid, jdata in scheduled_jobs.items():
        try:
            job = scheduler.get_job(jid)
            jdata['next_run'] = str(job.next_run_time) if job else 'N/A'
        except Exception:
            jdata['next_run'] = 'N/A'
        result.append(jdata)
    return result
