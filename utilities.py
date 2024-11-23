import numpy as np

def calculate_distance(measured_intensity, reference_intensity=1.0, reference_distance=1.0):
    """
    Calculate distance to sound source using inverse square law.
    
    Args:
        measured_intensity (float): Measured intensity at the microphone
        reference_intensity (float): Known reference intensity (default: 1.0)
        reference_distance (float): Known distance at reference intensity in meters (default: 1.0)
    
    Returns:
        float: Estimated distance to source in meters
    """
    return reference_distance * np.sqrt(reference_intensity / measured_intensity)

if __name__ == "__main__":
    # Test values
    I = 0.25  # Measured intensity (arbitrary unit)
    distance = calculate_distance(I)
    print(f"Estimated distance to source: {distance:.2f} meters")