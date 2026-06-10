import eventlet
eventlet.monkey_patch()
import logging
import atexit
from flask import Flask, render_template
from extensions import socketio
from config import Config
from scheduler import init_scheduler, shutdown_scheduler
from sockets import register_socket_events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

socketio.init_app(app)
# Register blueprints
from routes.capture import bp as capture_bp
from routes.scan import bp as scan_bp
from routes.schedule import bp as schedule_bp
from routes.captures import bp as captures_bp
from routes.system import bp as system_bp
from routes.bugreports import bp as bugreports_bp

app.register_blueprint(capture_bp)
app.register_blueprint(scan_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(captures_bp)
app.register_blueprint(system_bp)
app.register_blueprint(bugreports_bp)

# Register socket events
register_socket_events(socketio)

# Scheduler
init_scheduler()
atexit.register(shutdown_scheduler)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)