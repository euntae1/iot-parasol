import socket
import threading
import subprocess
import time
import pigpio


# ========== CAMERA STREAM START ======================================

def start_rpicam_stream():
    cmd = [
        "rpicam-vid",
        "-t", "0",
        "--inline",
        "--codec", "mjpeg",
        "--listen",
        "-o", "tcp://0.0.0.0:5003"
    ]
    subprocess.Popen(cmd)
    print("[PI] Pi camera streaming at tcp://0.0.0.0:5003")


# ========== MOTOR CONFIG =============================================

HORIZ_PIN = 12
VERT_PIN  = 13

MAX_HORIZ = 270
MAX_VERT  = 180

# θ는 60 / 90 / 120 세 값만 올 거라고 가정하고,
# 한 번에 최대 30도까지만 움직이도록 설정
MOVE_LIMIT = 60
QUANT = 10          # ★ 10도 단위 양자화 !!
UPDATE_INTERVAL = 1

MIN_PW = 600
MAX_PW = 2400

def angle_to_pw(angle, max_angle):
    angle = max(0, min(max_angle, angle))
    return int(MIN_PW + (MAX_PW - MIN_PW) * (angle / max_angle))


# ========== MOTOR CONTROL THREAD ======================================

current_vert = 90
current_horiz = 135

target_vert = None
target_horiz = None

motor_lock = threading.Lock()

def motor_thread():
    global current_vert, current_horiz
    global target_vert, target_horiz

    pi = pigpio.pi()
    if not pi.connected:
        print("[PI] ERROR: pigpio not running. Run: sudo pigpiod")
        return

    print("[PI] Motor thread started.")

    while True:
        time.sleep(UPDATE_INTERVAL)

        with motor_lock:
            tv = target_vert
            th = target_horiz

        if tv is None and th is None:
            print("[PI] Motor: both None → keep previous")
            continue

        # --- 10도 단위 양자화 적용 ---
        tv_q = round(tv / QUANT) * QUANT if tv is not None else None
        th_q = round(th / QUANT) * QUANT if th is not None else None

        if tv_q is not None:
            dv = max(-MOVE_LIMIT, min(MOVE_LIMIT, tv_q - current_vert))
            current_vert += dv

        if th_q is not None:
            dh = max(-MOVE_LIMIT, min(MOVE_LIMIT, th_q - current_horiz))
            current_horiz += dh

        pw_v = angle_to_pw(current_vert, MAX_VERT)
        pw_h = angle_to_pw(current_horiz, MAX_HORIZ)

        pi.set_servo_pulsewidth(VERT_PIN, pw_v)
        pi.set_servo_pulsewidth(HORIZ_PIN, pw_h)

        print(f"[PI] Motor → VERT={current_vert}, HORIZ={current_horiz}")


# ========== TCP SERVER =================================================

def recv_thread():
    global target_vert, target_horiz

    HOST = "0.0.0.0"
    PORT = 9003

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)

    print("[PI] Waiting for θ_r, φ_r on 0.0.0.0:9003...")
    conn, addr = server.accept()
    print("[PI] Connected by", addr)

    while True:
        data = conn.recv(1024)
        if not data:
            break

        try:
            msg = data.decode().strip()
            parts = msg.split(',')
            th_s = parts[0].split(':')[1]
            ph_s = parts[1].split(':')[1]

            theta_r = None if th_s == "None" else float(th_s)
            phi_r   = None if ph_s == "None" else float(ph_s)

            print(f"[PI] recv θ_r={theta_r}, φ_r={phi_r}")

            #----- 변환 없이 그대로 모터 입력 -----
            with motor_lock:

                if theta_r is not None:
                    target_vert = max(0, min(180, theta_r))

                if phi_r is not None:
                    target_horiz = max(0, min(270, phi_r))

        except Exception as e:
            print("[PI] Parse error:", e)

    conn.close()


# ========== MAIN ========================================================

if __name__ == "__main__":
    start_rpicam_stream()

    threading.Thread(target=motor_thread, daemon=True).start()
    recv_thread()

