from flask import Flask, Response
from picamera2 import Picamera2
import io

app = Flask(__name__)
picam = Picamera2()
picam.configure(picam.create_preview_configuration(main={"size": (640, 480)}))
picam.start()

def generate_frames():
    while True:
        buffer = io.BytesIO()
        picam.capture_file(buffer, format='jpeg')
        buffer.seek(0)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.read() + b'\r\n')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '<html><body><img src="/video" width="100%"></body></html>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
