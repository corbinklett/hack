import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def read_and_process_data(file_path, max_freq=10000):
    """Read CSV and process frequency data"""
    df = pd.read_csv(file_path)
    print(f"DataFrame shape: {df.shape}")
    frequencies = [float(col.replace(' Hz', '')) for col in df.columns[1:]]
    
    # Create frequency mask
    freq_mask = [f <= max_freq for f in frequencies]
    filtered_frequencies = [f for f, mask in zip(frequencies, freq_mask) if mask]
    
    return df, frequencies, freq_mask, filtered_frequencies

def calculate_powers(df, freq_mask):
    """Calculate total power for each distance"""
    powers = []
    for _, row in df.iterrows():
        power = np.sum(row[1:].values[freq_mask]**2)
        powers.append(power)
    return powers

def plot_fft_amplitudes(df, filtered_frequencies, freq_mask):
    """Create FFT amplitude plot"""
    plt.figure(figsize=(12, 6))
    for _, row in df.iterrows():
        distance = row['Distance']
        amplitudes_db = 20 * np.log10(row[1:].values[freq_mask])
        plt.plot(filtered_frequencies, amplitudes_db, label=f'Distance={distance}')

    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude (dB)')
    plt.title('FFT Amplitudes vs Frequency (in dB) [0-10kHz]')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

def plot_power_distance(distances, powers):
    """Create power vs distance plot"""
    plt.figure(figsize=(12, 6))
    # Convert powers to dB
    powers_db = 20 * np.log10(powers)
    plt.plot(distances, powers_db, 'b.-')
    plt.xlabel('Distance')
    plt.ylabel('Total Signal Power (dB)')
    plt.title('Total Signal Power vs Distance')
    plt.grid(True)
    plt.tight_layout()

def match_signal_shape(measured_fft, df, freq_mask, reference_distance=2):
    """
    Match measured FFT data against reference signal shape at distance=2
    
    Parameters:
    -----------
    measured_fft : array-like
        FFT amplitudes of the measured signal
    df : pandas DataFrame
        Reference data containing known signals
    freq_mask : array-like
        Frequency mask for filtering
    reference_distance : float
        Distance of reference signal to match against (default=2)
    
    Returns:
    --------
    matched_signal : array-like
        The portion of the signal that matches the reference shape
    correlation : float
        Correlation coefficient indicating match quality (0-1)
    """
    # Get reference signal for distance=2
    reference = df[df['Distance'] == reference_distance].iloc[0][1:].values[freq_mask]

    # assume the measured comes in masked, if necessary
    measured = measured_fft #[freq_mask]
    
    # Normalize both signals to unit norm
    reference_normalized = reference / np.linalg.norm(reference)
    measured_normalized = measured / np.linalg.norm(measured)
    
    # Pad reference if shorter than measured
    if len(reference_normalized) < len(measured_normalized):
        padding = np.zeros(len(measured_normalized) - len(reference_normalized))
        reference_normalized = np.concatenate([reference_normalized, padding])

    # Calculate correlation coefficient
    correlation = np.corrcoef(reference_normalized, measured_normalized)[0,1]
    
    # Create matched signal by scaling reference to match measured signal's energy
    scale_factor = np.linalg.norm(measured) / np.linalg.norm(reference)
    matched_signal = reference * scale_factor
    
    return matched_signal, correlation

def plot_signal_comparison(measured_fft, matched_signal, filtered_frequencies, freq_mask):
    """Plot original and matched signals for comparison"""
    plt.figure(figsize=(12, 6))
    
    # Plot original measured signal
    measured = measured_fft[freq_mask]
    plt.plot(filtered_frequencies, 20 * np.log10(measured), 
             label='Measured Signal', alpha=0.7)
    
    # Plot matched signal
    plt.plot(filtered_frequencies, 20 * np.log10(matched_signal), 
             label='Matched Signal', linestyle='--', alpha=0.7)
    
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude (dB)')
    plt.title('Signal Shape Matching Comparison')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

def main():
    # Read and process data
    df, frequencies, freq_mask, filtered_frequencies = read_and_process_data('fft_amplitudes_1.csv')
    
    # Create a noisier test signal
    base_signal = df.iloc[3][1:].values  # Using row at index 3 as base
    noise_level = 0.5  # Increased noise level
    measured_fft = base_signal + np.random.normal(0, noise_level, len(base_signal))
    
    # Add some artificial peaks to make it more interesting
    random_peaks = np.random.randint(0, len(measured_fft), 5)  # Add 5 random peaks
    measured_fft[random_peaks] *= 2.0
    
    # Match signal shape
    matched_signal, correlation = match_signal_shape(measured_fft, df, freq_mask)
    print(f"Shape correlation: {correlation:.3f}")
    
    # Plot comparison
    plot_signal_comparison(measured_fft, matched_signal, filtered_frequencies, freq_mask)
    plt.show()

if __name__ == "__main__":
    main()
