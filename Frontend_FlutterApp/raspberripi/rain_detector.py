# rain_detector.py
import subprocess

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
    print("Camera stream started.")

if __name__ == "__main__":
    start_rpicam_stream()
    while True:
        pass
