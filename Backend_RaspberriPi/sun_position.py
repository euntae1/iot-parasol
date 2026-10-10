# sun_position.py
# Utility functions to get sun position using pvlib

from datetime import datetime, timezone
import pvlib


def get_sun_angles(latitude, longitude, altitude):
    """
    Compute current sun position (altitude, azimuth) for given location.

    Returns:
        time_utc (datetime, timezone-aware UTC)
        altitude_deg (float): apparent elevation angle in degrees
        azimuth_deg (float): azimuth angle in degrees
    """
    time_utc = datetime.now(timezone.utc)

    solpos = pvlib.solarposition.get_solarposition(
        time=time_utc,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude
    )

    altitude_angle = float(solpos["apparent_elevation"].values[0])
    azimuth_angle = float(solpos["azimuth"].values[0])

    return time_utc, altitude_angle, azimuth_angle
