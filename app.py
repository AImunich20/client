from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import numpy as np
import base64
import threading
import time
from door import run_terminal

app = Flask(__name__)
app.secret_key = "admin"
run_terminal(app)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {}
last_seen = {}
lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('frame')
def handle_frame(data):
    client_id = data.get('clientId', 'unknown')
    buffer = data.get('buffer', None)
    if not buffer:
        return

    img = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is not None:
        with lock:
            clients[client_id] = img
            last_seen[client_id] = time.time()

def show_frames():
    while True:
        current_time = time.time()
        with lock:
            for client_id in list(clients.keys()):
                if current_time - last_seen.get(client_id, 0) > 2:
                    if cv2.getWindowProperty(f"Client: {client_id}", cv2.WND_PROP_VISIBLE) >= 0:
                        cv2.destroyWindow(f"Client: {client_id}")
                    del clients[client_id]
                    del last_seen[client_id]
                    continue

                frame = clients[client_id]
                cv2.imshow(f"Client: {client_id}", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

if __name__ == '__main__':
    t = threading.Thread(target=show_frames)
    t.daemon = True
    t.start()
    socketio.run(app, host='0.0.0.0', port=5400, debug=True)
