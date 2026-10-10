# ===========================================
# REAL.PY - 최종 통합본
# ===========================================
import cv2
import numpy as np
import threading
import time
import math
import requests

Width, Height = 320, 240

# ===============================
# 공유 변수
# ===============================
picam_frame = None
esp32_frame = None
frame_lock = threading.Lock()

ax_raw = None
ay_raw = None
ax_smooth = None
ay_smooth = None
angle_lock = threading.Lock()

theta_global = None
phi_global = None

stop_flag = False

# ===============================
# Sobel Filters
# ===============================
x_filter = np.array([[-1,0,1],[-1,0,1],[-1,0,1]], np.float32)
y_filter = np.array([[-1,-1,-1],[0,0,0],[1,1,1]], np.float32)

def conv2(img, kernel):
    return cv2.filter2D(img, cv2.CV_32F, kernel)

def round1(x):
    return None if x is None else round(float(x), 1)


# ==========================================================
# detect angle 
# ==========================================================
def detect_motor_angle(prev_gray, gray, frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h,s,v = cv2.split(hsv)
    mask_color = ((s < 90) & (v > 120)).astype(np.uint8)

    flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None,
                    0.5,3,15,3,5,1.2,0)

    fx, fy = flow[...,0], flow[...,1]
    flow_mag = np.sqrt(fx*fx + fy*fy)
    flow_ang = (np.degrees(np.arctan2(fy, fx)) + 360) % 360

    grad_x = conv2(gray, x_filter)
    grad_y = conv2(gray, y_filter)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    grad_ang = (np.degrees(np.arctan2(grad_y, grad_x)) + 360) % 360

    streak_ang = (grad_ang + 90) % 360

    flow_thr = 1.5
    grad_thr = 10
    angle_center = 90
    angle_range = 45

    hist = {}

    for y in range(0, Height, 2):
        for x in range(0, Width, 2):

            if mask_color[y,x] == 0: continue
            if flow_mag[y,x] < flow_thr: continue
            if grad_mag[y,x] < grad_thr: continue

            ga = streak_ang[y,x]
            if not (angle_center - angle_range <= ga <= angle_center + angle_range):
                continue

            fa = flow_ang[y,x]
            if not (angle_center - angle_range <= fa <= angle_center + angle_range):
                continue

            bin_ang = int(round(fa)) % 360
            hist[bin_ang] = hist.get(bin_ang, 0) + 1

    if len(hist) == 0:
        return None

    total = sum(hist.values())
    avg = sum(k*v for k,v in hist.items()) / total

    return round(avg, 1)


# ==========================================================
# smoothing thread
# ==========================================================
def smoothing_thread():
    global ax_raw, ay_raw, ax_smooth, ay_smooth
    STEP_LIMIT = 10

    while not stop_flag:
        with angle_lock:

            if ax_raw is not None:
                if ax_smooth is None:
                    ax_smooth = ax_raw
                diff = ax_raw - ax_smooth
                diff = max(-STEP_LIMIT, min(STEP_LIMIT, diff))
                ax_smooth = round1(ax_smooth + diff)

            if ay_raw is not None:
                if ay_smooth is None:
                    ay_smooth = ay_raw
                diff = ay_raw - ay_smooth
                diff = max(-STEP_LIMIT, min(STEP_LIMIT, diff))
                ay_smooth = round1(ay_smooth + diff)

        time.sleep(1)


# ==========================================================
# θ / φ 계산
# ==========================================================
def theta_from_single(a):
    if a is None:
        return None
    if a > 95: return 120.0
    if a < 85: return 60.0
    return 90.0


def compute_theta_phi(ax, ay):
    print(f"ax={ax}, ay={ay}")
    if ax is None and ay is None:
        return None, None

    if ay is None:
        return theta_from_single(ax), 90.0

    if ax is None:
        return theta_from_single(ay), 180.0

    dx = ax - 90.0
    dy = ay - 90.0
    eps = 1e-6

    if abs(dx) < eps and abs(dy) < eps:
        phi = 90.0
    elif abs(dx) < eps:
        phi = 0.0 if dy > 0 else 180.0
    elif abs(dy) < eps:
        phi = 90.0
    else:
        phi = 135.0 if dx * dy > 0 else 45.0

    tx = theta_from_single(ax)
    ty = theta_from_single(ay)

    if tx == ty:
        theta = tx
    else:
        if tx == 120.0:
            theta = 120.0
        elif ty == 120.0:
            theta = 60.0
        else:
            theta = 60.0

    return theta, phi


# ==========================================================
# PiCam Thread
# ==========================================================
def picam_thread(url):
    global picam_frame, ax_raw

    cap = cv2.VideoCapture(url)
    prev = None

    while not stop_flag:
        ret, frame = cap.read()
        if not ret: continue

        frame = cv2.resize(frame, (Width, Height))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        with frame_lock:
            picam_frame = frame.copy()

        if prev is not None:
            ax = detect_motor_angle(prev, gray, frame)
            with angle_lock:
                ax_raw = ax

        prev = gray


# ==========================================================
# ESP32 Thread
# ==========================================================
def esp32_thread(url):
    global esp32_frame, ay_raw

    cap = cv2.VideoCapture(url)
    prev = None

    while not stop_flag:
        ret, frame = cap.read()
        if not ret: continue

        frame = cv2.resize(frame, (Width, Height))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        with frame_lock:
            esp32_frame = frame.copy()

        if prev is not None:
            ay = detect_motor_angle(prev, gray, frame)
            with angle_lock:
                ay_raw = ay

        prev = gray


# ==========================================================
# HTTP POST 송신
# ==========================================================
def send_thread(pi_ip):
    global theta_global, phi_global

    url = f"http://{pi_ip}:5001/rain_angle"

    while not stop_flag:

        with angle_lock:
            ax = ax_smooth
            ay = ay_smooth

        # 카메라 스왑
        real_ax = ay      # rpi cam → y축
        real_ay = ax      # esp32 → x축

        theta, phi = compute_theta_phi(real_ax, real_ay)

        theta_global, phi_global = theta, phi

        data = {"theta": theta, "phi": phi}
        requests.post(url, json=data)

        print(f"[SEND] θ={theta}, φ={phi}")

        time.sleep(1)


# ==========================================================
# UI Display
# ==========================================================
def main_loop():
    global stop_flag

    while True:
        with frame_lock:
            f1 = None if picam_frame is None else picam_frame.copy()
            f2 = None if esp32_frame is None else esp32_frame.copy()

        if f1 is not None:
            cv2.imshow("PiCam", f1)
        if f2 is not None:
            cv2.imshow("ESP32", f2)

        if cv2.waitKey(1) == ord('q'):
            stop_flag = True
            break

        time.sleep(0.01)

    cv2.destroyAllWindows()


# ==========================================================
# 실행
# ==========================================================
if __name__ == "__main__":

    PI_IP = "172.20.10.2"
    PICAM_URL = "tcp://172.20.10.2:5003"
    ESP32_URL = "http://172.20.10.4:81/stream"

    threading.Thread(target=smoothing_thread, daemon=True).start()
    threading.Thread(target=picam_thread, args=(PICAM_URL,), daemon=True).start()
    threading.Thread(target=esp32_thread, args=(ESP32_URL,), daemon=True).start()
    threading.Thread(target=send_thread, args=(PI_IP,), daemon=True).start()

    main_loop()
