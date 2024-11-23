import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from queue import Queue, Empty
import threading
from scipy.fft import fft

# Parameters
sample_rate = 44100  # Sampling rate in Hz
duration = 0.1       # Duration of each chunk in seconds
buffer_size = int(sample_rate * duration)  # Number of samples per chunk

# Modified plot setup
def setup_plot(buffer_size):
    global ax1, ax2  # Make axes global
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Time domain plot
    x = np.arange(0, buffer_size) / sample_rate
    line_time, = ax1.plot(x, np.zeros(buffer_size), '-')
    ax1.set_ylim(-1, 1)
    ax1.set_xlim(0, buffer_size/sample_rate)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude")
    ax1.set_title("Real-Time Audio Signal")
    
    # Frequency domain plot
    freqs = np.fft.fftfreq(buffer_size, 1/sample_rate)
    line_freq, = ax2.plot(freqs[:buffer_size//2], np.zeros(buffer_size//2), '-')
    ax2.set_xlim(0, sample_rate/2)  # Only show positive frequencies up to Nyquist
    ax2.set_ylim(0, 1)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude")
    ax2.set_title("Real-Time FFT")
    
    plt.tight_layout()
    return fig, line_time, line_freq

# Create a queue for communication between threads
data_queue = Queue()

# Modified callback function that only puts data in queue
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    data_queue.put(indata[:, 0])

# Modified update_plot function
def update_plot():
    while True:
        try:
            data = data_queue.get_nowait()
            
            # Resize data arrays if input size changes
            if len(data) != buffer_size:
                # Update time domain plot
                x_new = np.arange(0, len(data)) / sample_rate
                line_time.set_xdata(x_new)
                line_time.set_ydata(data)
                
                # Update frequency domain plot
                freqs_new = np.fft.fftfreq(len(data), 1/sample_rate)
                fft_data = fft(data)
                fft_mag = np.abs(fft_data[:len(data)//2]) / len(data)
                line_freq.set_xdata(freqs_new[:len(data)//2])
                line_freq.set_ydata(fft_mag)
                
                # Update axis limits
                ax1.set_xlim(0, len(data)/sample_rate)
                ax2.set_xlim(0, sample_rate/2)
            else:
                # Normal update without resizing
                line_time.set_ydata(data)
                fft_data = fft(data)
                fft_mag = np.abs(fft_data[:len(data)//2]) / len(data)
                line_freq.set_ydata(fft_mag)
            
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
        except Empty:
            break

# Initialize plot with a default size
buffer_size = 1024  # Starting buffer size
fig, line_time, line_freq = setup_plot(buffer_size)  # Updated unpacking
x = np.arange(0, buffer_size) / sample_rate

# Start the audio stream
try:
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate):
        print("Streaming audio... Press Ctrl+C to stop.")
        while True:
            update_plot()
            plt.pause(0.01)
except KeyboardInterrupt:
    print("Stopped streaming.")