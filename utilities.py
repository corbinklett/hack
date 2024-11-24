import numpy as np

def calculate_distance(measured_db, reference_db=94.0, reference_distance=1.0):
    """
    Calculate distance to sound source using inverse square law, taking decibel measurements.
    
    Args:
        measured_db (float): Measured sound pressure level in dB
        reference_db (float): Reference sound pressure level in dB (default: 94.0 dB, typical calibrator level)
        reference_distance (float): Known distance at reference measurement in meters (default: 1.0)
    
    Returns:
        float: Estimated distance to source in meters
    
    Note:
        This function assumes measurements are sound pressure levels (SPL) referenced to 20 µPa.
        The default reference of 94 dB is a common calibrator level.
    """
    # Convert dB to intensity ratio
    # Using P1/P2 = 10^((dB1-dB2)/20)
    pressure_ratio = 10 ** ((reference_db - measured_db) / 20)
    
    # Apply inverse square law
    return reference_distance * np.sqrt(pressure_ratio)

if __name__ == "__main__":
    # Test values
    measured_spl = 88.0  # Example: 88 dB SPL
    distance = calculate_distance(measured_spl)
    print(f"Estimated distance to source: {distance:.2f} meters")