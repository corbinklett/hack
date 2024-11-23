import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from queue import Queue, Empty
import threading

# Parameters
sample_rate = 44100  # Sampling rate in Hz
duration = 0.1       # Duration of each chunk in seconds
buffer_size = int(sample_rate * duration)  # Number of samples per chunk

# Modified plot setup
def setup_plot(buffer_size):
    plt.ion()
    fig, ax = plt.subplots()
    x = np.arange(0, buffer_size) / sample_rate
    line, = ax.plot(x, np.zeros(buffer_size), '-')
    ax.set_ylim(-1, 1)
    ax.set_xlim(0, buffer_size/sample_rate)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    plt.title("Real-Time Audio Signal")
    return fig, line

# Create a queue for communication between threads
data_queue = Queue()

# Modified callback function that only puts data in queue
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    data_queue.put(indata[:, 0])

# Modified update_plot function
def update_plot():
    global x, line  # Move global declaration to start of function
    while True:
        try:
            data = data_queue.get_nowait()
            if len(data) != len(x):  # If data size changes
                x = np.arange(0, len(data)) / sample_rate
                line.set_xdata(x)
            line.set_ydata(data)
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
        except Empty:
            break

# Initialize plot with a default size
buffer_size = 1024  # Starting buffer size
fig, line = setup_plot(buffer_size)
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