import logging
import scanner
from flask_socketio import emit
from device import check_rtlsdr

logger = logging.getLogger(__name__)


def register_socket_events(socketio):

    @socketio.on('connect')
    def on_connect():
        ok, msg = check_rtlsdr()
        emit('device_status', {"connected": ok, "message": msg})
        logger.info(f"Client connected - device status: {msg}")

    @socketio.on('disconnect')
    def on_disconnect():
        logger.info("Client disconnected")

    @socketio.on('ping_scan')
    def ping_scan():
        emit('scan_status', {"active": scanner.scan_active})


