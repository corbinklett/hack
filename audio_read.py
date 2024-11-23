import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from queue import Queue, Empty
import threading
from scipy.fft import fft
from utilities import calculate_distance

# Parameters
sample_rate = 44100
duration = 0.1
buffer_size = int(sample_rate * duration)

# Modified frequency band to focus on 440 Hz
freq_min = 2700  # Hz (440 Hz ± 5 Hz)
freq_max = 3200  # Hz
ref_db = 94.0    # Reference dB for distance calculation

def setup_plot(buffer_size):
    global ax1, ax2, ax3
    plt.ion()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    
    # Time domain plot
    x = np.arange(buffer_size) / sample_rate
    line_time, = ax1.plot(x, np.zeros(buffer_size), '-')
    ax1.set_ylim(-1, 1)
    ax1.set_xlim(0, duration)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude")
    ax1.set_title("Real-Time Audio Signal")
    
    # Frequency domain plot
    freqs = np.fft.fftfreq(buffer_size, 1/sample_rate)
    line_freq, = ax2.plot(freqs[:buffer_size//2], np.zeros(buffer_size//2), '-')
    ax2.set_xlim(0, sample_rate/2)
    ax2.set_ylim(0, 1)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude")
    ax2.set_title("Real-Time FFT")
    
    # Distance plot - Create initial empty arrays of the correct size
    max_points = int(30/duration)  # Number of points for 30 seconds
    line_dist, = ax3.plot(np.zeros(max_points), np.zeros(max_points), '-')
    ax3.set_xlim(0, 30)
    ax3.set_ylim(0, 10)
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Distance (m)")
    ax3.set_title(f"Estimated Distance (for {freq_min}-{freq_max} Hz)")
    
    plt.tight_layout()
    return fig, line_time, line_freq, line_dist

# Create a queue for communication between threads
data_queue = Queue()

# Modified callback function that only puts data in queue
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    data_queue.put(indata[:, 0])

def get_band_energy(fft_data, freqs):
    """Calculate energy in specified frequency band with improved filtering"""
    mask = (freqs >= freq_min) & (freqs <= freq_max)
    # Apply Hanning window to reduce spectral leakage
    window = np.hanning(np.sum(mask))
    return np.mean(np.abs(fft_data[mask]) * window) * 20

# Modified update_plot function
def update_plot():
    global distance_history, time_history
    current_time = 0
    max_points = int(30/duration)  # Number of points for 30 seconds
    distance_history = np.zeros(max_points)  # Pre-allocate arrays
    time_history = np.zeros(max_points)
    
    while True:
        try:
            data = data_queue.get_nowait()
            current_time += duration
            
            # Ensure data length matches buffer_size
            if len(data) != buffer_size:
                data = np.resize(data, buffer_size)
            
            # Update time and frequency domain plots
            line_time.set_ydata(data)
            fft_data = fft(data)
            freqs = np.fft.fftfreq(len(data), 1/sample_rate)[:len(data)//2]
            fft_mag = np.abs(fft_data[:len(data)//2]) / len(data)
            line_freq.set_ydata(fft_mag)
            
            # Calculate band energy and convert to dB
            band_energy = get_band_energy(fft_data[:len(data)//2], freqs)
            db_level = 20 * np.log10(band_energy) + ref_db
            
            # Calculate and plot distance
            distance = calculate_distance(db_level, reference_db=ref_db)
            distance_history = np.roll(distance_history, -1)
            distance_history[-1] = distance
            time_history = np.roll(time_history, -1)
            time_history[-1] = current_time
            
            # Keep only last 30 seconds of data
            if current_time > 30:
                distance_history = distance_history[-int(30/duration):]
                time_history = time_history[-int(30/duration):]
            
            line_dist.set_data(time_history, distance_history)
            
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            
        except Empty:
            break

# Initialize plot
buffer_size = int(sample_rate * duration)
fig, line_time, line_freq, line_dist = setup_plot(buffer_size)

# Start the audio stream
try:
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate):
        print("Streaming audio... Press Ctrl+C to stop.")
        while True:
            update_plot()
            plt.pause(0.01)
except KeyboardInterrupt:
    print("Stopped streaming.")