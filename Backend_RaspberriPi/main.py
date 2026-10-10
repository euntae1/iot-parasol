# main.py
# Main loop: get sun position (pvlib) and move servos (pigpio)

import time

from sun_position import get_sun_angles
from servo_controller import ServoTracker


# ===== Location (will replace with GPS later) =====

LATITUDE  = 52.5200     # Berlin latitude
LONGITUDE = 13.4050     # Berlin longitude
ALTITUDE  = 34          # altitude in meters
      

# Tracking parameters
TRACK_INTERVAL = 10.0   # seconds between updates
DEADZONE_DEG   = 1.0    # do not move if change < 1 deg


def main():
    # Initialize servo tracker
    tracker = ServoTracker()
    print("ServoTracker initialized.")
    print(f"Location: lat={LATITUDE}, lon={LONGITUDE}, alt={ALTITUDE} m")

    try:
        while True:
            time_utc, altitude_deg, azimuth_deg = get_sun_angles(
                LATITUDE, LONGITUDE, ALTITUDE
            )

            print(f"\nUTC time: {time_utc}")
            print(f"Sun altitude: {altitude_deg:.2f} deg, azimuth: {azimuth_deg:.2f} deg")

            if altitude_deg <= 0:
                print("Sun below horizon -> parking at 0 deg.")
                tracker.park()
            else:
                print("Moving servos toward sun (smooth)...")
                tracker.move_to_sun_smooth(
                    altitude_deg,
                    azimuth_deg,
                    deadzone_deg=DEADZONE_DEG,
                    step_deg=0.5,      # smaller -> more steps, smoother & slower
                    step_delay=0.01    # larger -> slower
                )

            time.sleep(TRACK_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        tracker.stop()
        print("Servos off, pigpio stopped.")


if __name__ == "__main__":
    main()
