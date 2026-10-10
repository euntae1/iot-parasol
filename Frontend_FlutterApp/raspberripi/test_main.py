# ============================================================
#test_server.py
# SMART PARASOL – FINAL SERVER INTEGRATION
# SUNNY MODE + RAIN MODE + MANUAL + SMOOTH CONTROL THREAD
# ============================================================

from flask import Flask, request, jsonify
import threading
import time
from datetime import datetime

from test_sun_position import get_sun_angles
from test_servo_controller import ServoTracker

app = Flask(__name__)

LAT = 37.5665
LON = 126.9780
ALT = 50

tracker = ServoTracker()
motion_lock = threading.Lock()

shared = {
    "utc_time": "",
    "sun_altitude": 0.0,
    "sun_azimuth": 0.0,

    "umbrella_rotation": 0.0,
    "umbrella_rotation_user": 0.0,
    "umbrella_tilt": 0.0,

    "suggested_rotation": 0.0,
    "suggested_tilt": 0.0,

    "target_rot": None,
    "target_tilt": None,

    "mode": "manual",
    "is_raining": False,

    "force_night": None
}

def check_night():
    if shared["force_night"] is True:
        return True
    if shared["force_night"] is False:
        return False

    hour = datetime.now().hour
    return (hour < 6 or hour >= 18)

def normalize_user_rotation(user_rot):
    user_rot = user_rot % 360
    if user_rot > 180:
        user_rot -= 180
    return user_rot

def map_user_rotation_to_motor(user_rot_norm):
    return max(0, min(270, user_rot_norm * (200.0 / 180.0)))

def normalize_user_tilt(raw_rot, raw_tilt):
    if raw_rot <= 180:
        return raw_tilt
    return 180 - raw_tilt

def servo_thread():
    while True:
        with motion_lock:
            tr = shared["target_rot"]
            tt = shared["target_tilt"]

        if tr is not None and tt is not None:
            tracker._smooth_move_to_angles(
                tr, tt,
                step_deg=1.7,
                step_delay=0.03
            )

            shared["umbrella_rotation"] = tr
            shared["umbrella_tilt"] = tt

        time.sleep(0.05)

threading.Thread(target=servo_thread, daemon=True).start()

def tracking_loop():
    while True:
        if shared["mode"] == "sun":
            t_utc, alt, az = get_sun_angles(LAT, LON, ALT)
            az = (360 - az) % 360

            shared["utc_time"] = t_utc.isoformat()
            shared["sun_altitude"] = alt
            shared["sun_azimuth"] = az

            shared["suggested_rotation"] = az
            shared["suggested_tilt"] = alt

        time.sleep(0.2)

threading.Thread(target=tracking_loop, daemon=True).start()

@app.route("/rain_angle", methods=["POST"])
def rain_angle():
    data = request.get_json()
    theta = float(data["theta"])
    phi = float(data["phi"])

    shared["is_raining"] = True
    if shared["mode"] != "rain":
        return jsonify({"status": "ignored"})

    raw_rot = phi
    raw_tilt = theta

    user_rot_norm = normalize_user_rotation(raw_rot)
    tilt_norm = normalize_user_tilt(raw_rot, raw_tilt)

    motor_rot = map_user_rotation_to_motor(user_rot_norm)
    motor_tilt = tilt_norm

    with motion_lock:
        shared["target_rot"] = motor_rot
        shared["target_tilt"] = motor_tilt

        shared["umbrella_rotation_user"] = raw_rot
        shared["umbrella_tilt_user"] = raw_tilt

    return jsonify({"status": "rain applied"})

@app.route("/go_suggested", methods=["POST"])
def go_suggested():
    rot = shared["suggested_rotation"]
    tilt = shared["suggested_tilt"]

    user_rot_norm = normalize_user_rotation(rot)
    tilt_norm = normalize_user_tilt(rot, tilt)

    motor_rot = map_user_rotation_to_motor(user_rot_norm)
    motor_tilt = tilt_norm

    with motion_lock:
        shared["target_rot"] = motor_rot
        shared["target_tilt"] = motor_tilt

        shared["umbrella_rotation_user"] = rot
        shared["umbrella_tilt_user"] = tilt

    return jsonify({"status": "moving to suggested"})

@app.route("/manual", methods=["POST"])
def manual_move():
    data = request.get_json()
    raw_rot = float(data["rotation"])
    raw_tilt = float(data["tilt"])

    shared["mode"] = "manual"

    user_rot_norm = normalize_user_rotation(raw_rot)
    tilt_norm = normalize_user_tilt(raw_rot, raw_tilt)

    motor_rot = map_user_rotation_to_motor(user_rot_norm)
    motor_tilt = tilt_norm

    with motion_lock:
        shared["target_rot"] = motor_rot
        shared["target_tilt"] = motor_tilt
        shared["umbrella_rotation_user"] = raw_rot
        shared["umbrella_tilt_user"] = raw_tilt

    return jsonify({"status": "manual ok"})

@app.route("/mode_sun", methods=["POST"])
def mode_sun():
    shared["mode"] = "sun"
    return jsonify({"status": "sun mode on"})

@app.route("/mode_rain", methods=["POST"])
def mode_rain():
    shared["mode"] = "rain"
    shared["is_raining"] = True
    return jsonify({"status": "rain mode on"})

@app.route("/mode_manual", methods=["POST"])
def mode_manual():
    shared["mode"] = "manual"
    return jsonify({"status": "manual mode on"})

@app.route("/force_day", methods=["POST"])
def force_day():
    shared["force_night"] = False
    return jsonify({"status": "forced day"})

@app.route("/force_night", methods=["POST"])
def force_night():
    shared["force_night"] = True
    return jsonify({"status": "forced night"})

@app.route("/force_auto", methods=["POST"])
def force_auto():
    shared["force_night"] = None
    return jsonify({"status": "force auto"})

@app.route("/status")
def status():
    shared["is_night"] = check_night()
    return jsonify(shared)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
