# servo_controller.py
# Servo control using pigpio for sun tracking

import time
import math
import pigpio


# ===== Servo hardware configuration =====
HORIZ_PIN = 17        # Horizontal servo (BCM 17) - azimuth axis
VERT_PIN  = 27        # Vertical servo (BCM 27) - altitude axis

MAX_HORIZ_ANGLE = 270.0   # Horizontal servo usable range (deg)
MAX_VERT_ANGLE  = 180.0   # Vertical servo usable range (deg)

# Invert flags (set True if servo direction is reversed for your setup)
HORIZ_INVERT = False
VERT_INVERT  = False

# Pulse width range for your servos (microseconds) - tune if needed
MIN_PW = 600      # pulse width for 0 deg
MAX_PW = 2400     # pulse width for max angle


class ServoTracker:
    """
    Servo controller for a 2-axis sun tracker using pigpio.
    Horizontal axis tracks azimuth, vertical axis tracks altitude.
    """

    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Cannot connect to pigpio daemon. Run 'sudo pigpiod' first.")

        # Logical current angles (deg) - we do NOT force servos to move at init
        self.current_horiz = 270.0
        self.current_vert  = 90.0
        # No initial _apply_angles() here: we don't touch servo position on startup
        

        

    # ---------- low-level helpers ----------

    def _angle_to_pulsewidth(self, angle, max_angle):
        """Map angle [0, max_angle] to pulse width [MIN_PW, MAX_PW]."""
        if angle < 0:
            angle = 0
        if angle > max_angle:
            angle = max_angle

        pw = MIN_PW + (MAX_PW - MIN_PW) * (angle / max_angle)
        return int(pw)

    def _apply_angles(self, horiz_angle, vert_angle):
        """
        Send pulse widths to both servos.
        horiz_angle, vert_angle are logical angles before inversion.
        """
        # Apply inversion if needed
        if HORIZ_INVERT:
            horiz_hw = MAX_HORIZ_ANGLE - horiz_angle
        else:
            horiz_hw = horiz_angle

        if VERT_INVERT:
            vert_hw = MAX_VERT_ANGLE - vert_angle
        else:
            vert_hw = vert_angle

        pw_h = self._angle_to_pulsewidth(horiz_hw, MAX_HORIZ_ANGLE)
        pw_v = self._angle_to_pulsewidth(vert_hw,  MAX_VERT_ANGLE)

        self.pi.set_servo_pulsewidth(HORIZ_PIN, pw_h)
        self.pi.set_servo_pulsewidth(VERT_PIN,  pw_v)

    # ---------- sun position → servo angles ----------

    def sun_to_servo_angles(self, altitude_deg, azimuth_deg):
        """
        Convert sun position (altitude, azimuth) to servo target angles.

        Assumptions:
        - Horizontal servo: 0–360 azimuth -> 0–MAX_HORIZ_ANGLE.
        - Vertical servo: 0–90 altitude  -> 0–MAX_VERT_ANGLE.
        """
        if altitude_deg <= 0:
            # Sun below horizon: park at 0 deg for both axes
            return 0.0, 0.0

        # Map azimuth 0–360 -> servo 0–MAX_HORIZ_ANGLE
        horiz_angle = azimuth_deg * (MAX_HORIZ_ANGLE / 360.0)

        # Map altitude 0–90 -> servo 0–MAX_VERT_ANGLE
        if altitude_deg > 90:
            altitude_deg = 90.0
        vert_angle = altitude_deg * (MAX_VERT_ANGLE / 90.0)

        return horiz_angle, vert_angle

    # ---------- 기존: 한 번에 점프하는 이동 ----------

    def move_to_sun(self, altitude_deg, azimuth_deg, deadzone_deg=1.0):
        """
        Move both servos toward the given sun position (single step).
        deadzone_deg: minimum angle difference to trigger movement.
        """
        target_horiz, target_vert = self.sun_to_servo_angles(altitude_deg, azimuth_deg)

        # Horizontal deadzone check
        if abs(target_horiz - self.current_horiz) > deadzone_deg:
            self.current_horiz = target_horiz

        # Vertical deadzone check
        if abs(target_vert - self.current_vert) > deadzone_deg:
            self.current_vert = target_vert

        # Apply (even if only one axis changed)
        self._apply_angles(self.current_horiz, self.current_vert)

    # ---------- 새로 추가: 부드럽게 이동 ----------

    def _smooth_move_to_angles(self, target_horiz, target_vert,
                               step_deg=1.0, step_delay=0.1):
        """
        Smoothly move from current_horiz/current_vert to target angles.

        step_deg: max angle change per step (deg)
        step_delay: delay between steps (seconds)
        """
        start_h = self.current_horiz
        start_v = self.current_vert

        delta_h = target_horiz - start_h
        delta_v = target_vert - start_v

        # nothing to do
        if abs(delta_h) < 1e-6 and abs(delta_v) < 1e-6:
            return

        # number of steps based on the larger movement
        steps_h = abs(delta_h) / step_deg if step_deg > 0 else 1
        steps_v = abs(delta_v) / step_deg if step_deg > 0 else 1
        steps = int(math.ceil(max(steps_h, steps_v)))
        if steps < 1:
            steps = 1

        for i in range(1, steps + 1):
            ratio = i / steps
            new_h = start_h + delta_h * ratio
            new_v = start_v + delta_v * ratio

            self._apply_angles(new_h, new_v)
            time.sleep(step_delay)

        # 최종 각도 업데이트
        self.current_horiz = target_horiz
        self.current_vert  = target_vert

    def move_to_sun_smooth(self, altitude_deg, azimuth_deg,
                           deadzone_deg=1.0,
                           step_deg=1.0,
                           step_delay=1.0):
        """
        Move servos toward given sun position with smooth motion.

        deadzone_deg: minimum angle difference to start movement
        step_deg: max angle per interpolation step (deg)
        step_delay: delay between steps (seconds)
        """
        target_horiz, target_vert = self.sun_to_servo_angles(altitude_deg, azimuth_deg)

        diff_h = abs(target_horiz - self.current_horiz)
        diff_v = abs(target_vert - self.current_vert)

        if diff_h <= deadzone_deg and diff_v <= deadzone_deg:
            return

        self._smooth_move_to_angles(target_horiz, target_vert,
                                    step_deg=step_deg,
                                    step_delay=step_delay)

    # ---------- 기타 유틸 ----------

    def park(self):
        """Park servos at 0 deg (smooth)."""
        self._smooth_move_to_angles(0.0, 0.0, step_deg=2.0, step_delay=0.02)

    def stop(self):
        """Turn off servo pulses and release pigpio."""
        self.pi.set_servo_pulsewidth(HORIZ_PIN, 0)
        self.pi.set_servo_pulsewidth(VERT_PIN, 0)
        self.pi.stop()
