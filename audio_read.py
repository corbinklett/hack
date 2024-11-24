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

# Modified frequency band to focus on target band
freq_min = 2000  # Hz
freq_max = 7000  # Hz
max_freq_collected = 10000  # Hz

def setup_plot(buffer_size):
    global ax1, ax2
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Time domain plot
    x = np.arange(buffer_size) / sample_rate
    line_time, = ax1.plot(x, np.zeros(buffer_size), '-')
    ax1.set_ylim(-1, 1)
    ax1.set_xlim(0, duration)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude")
    ax1.set_title("Real-Time Audio Signal")
    
    # Frequency domain plot - limit to 10000 Hz
    freqs = np.fft.fftfreq(buffer_size, 1/sample_rate)
    freq_mask = (freqs >= 0) & (freqs <= max_freq_collected)  # New mask for frequencies
    line_freq, = ax2.plot(freqs[freq_mask], np.zeros(np.sum(freq_mask)), '-')
    peak_point, = ax2.plot([], [], 'ro', markersize=10, label='Peak')
    ax2.set_xlim(0, max_freq_collected)  # Changed to 10000 Hz
    ax2.set_ylim(0, 1)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude")
    ax2.set_title("Real-Time FFT")
    ax2.legend()
    
    plt.tight_layout()
    return fig, line_time, line_freq, peak_point

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
    return 20 * np.log10(np.mean(np.abs(fft_data[mask])) + 1e-10)

# Modified update_plot function
def update_plot():
    while True:
        try:
            data = data_queue.get_nowait()
            
            # Ensure data length matches buffer_size
            if len(data) != buffer_size:
                data = np.resize(data, buffer_size)
            
            # Update time domain plot
            line_time.set_ydata(data)
            
            # Apply Hanning window before FFT
            window = np.hanning(len(data))
            windowed_data = data * window
            fft_data = fft(windowed_data)
            
            # Ensure consistent array sizes for frequency plot and limit to 10000 Hz
            freqs = np.fft.fftfreq(buffer_size, 1/sample_rate)
            freq_mask = (freqs >= 0) & (freqs <= max_freq_collected)  # New mask for frequencies
            fft_mag = np.abs(fft_data[freq_mask]) / buffer_size
            
            # Update frequency plot with matching sizes
            line_freq.set_ydata(fft_mag)
            
            # Find peak frequency (only within our displayed range)
            peak_idx = np.argmax(fft_mag)
            peak_freq = freqs[freq_mask][peak_idx]
            peak_magnitude = fft_mag[peak_idx]
            
            # Update peak point
            peak_point.set_data([peak_freq], [peak_magnitude])
            
            # Add text annotation for peak values
            ax2.set_title(f"Real-Time FFT (Peak: {peak_freq:.1f} Hz, Magnitude: {peak_magnitude:.3f})")
            
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            
        except Empty:
            break

# Initialize plot
buffer_size = int(sample_rate * duration)
fig, line_time, line_freq, peak_point = setup_plot(buffer_size)

# Start the audio stream
try:
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate):
        print("Streaming audio... Press Ctrl+C to stop.")
        while True:
            update_plot()
            plt.pause(0.01)
except KeyboardInterrupt:
    print("Stopped streaming.")