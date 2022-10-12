import threading
import time
from flask import Response
from flask import Flask
from flask import render_template
import cv2

app = Flask(__name__)

camera = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION) # Maybe change to 0 -> depends on camera source

outputFrame = None
outputFrame2 = None

lock = threading.Lock()


def do_slam_things():
    global camera, outputFrame, outputFrame2, lock

    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        with lock:
            outputFrame = frame.copy()
            outputFrame2 = gray.copy()

        time.sleep(0.0001)


def generate_frames():
    global outputFrame, lock

    while True:
        with lock:
            if outputFrame is None:
                continue

            ret, buffer = cv2.imencode('.jpg', outputFrame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  #

        time.sleep(0.0001)


def generate_frames2():
    global outputFrame2, lock

    while True:
        with lock:
            if outputFrame2 is None:
                continue

            ret, buffer = cv2.imencode('.jpg', outputFrame2)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  #

        time.sleep(0.0001)


@app.route("/")
def index():
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed2')
def video_feed2():
    return Response(generate_frames2(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    t = threading.Thread(target=do_slam_things, args=())
    t.daemon = True
    t.start()

    app.run(debug=True,
            threaded=True, use_reloader=False)