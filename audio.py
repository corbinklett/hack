import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from queue import Queue, Empty
from scipy.fft import fft

class AudioProcessor:
    def __init__(self, sample_rate=44100, duration=0.1, freq_min=00, freq_max=7000, max_freq_collected=10000):
        self.sample_rate = sample_rate
        self.duration = duration
        self.buffer_size = int(sample_rate * duration)
        self.freq_min = freq_min
        self.freq_max = freq_max
        self.max_freq_collected = max_freq_collected
        self.data_queue = Queue()

    def process_audio_data(self, audio_data):
        """Process raw audio data and return FFT results"""
        # Apply Hanning window before FFT
        window = np.hanning(len(audio_data))
        windowed_data = audio_data * window
        fft_data = fft(windowed_data)
        
        freqs = np.fft.fftfreq(self.buffer_size, 1/self.sample_rate)
        freq_mask = (freqs >= 0) & (freqs <= self.max_freq_collected)
        
        freqs = freqs[freq_mask]
        fft_data = fft_data[freq_mask]
        fft_mag = 20 * np.log10(np.abs(fft_data) + 1e-10)
        
        return freqs, fft_mag, fft_data

    def get_range_peak(self, fft_data, freqs, band_min, band_max):
        """Find peak frequency and power within specified frequency band"""
        mask = (freqs >= band_min) & (freqs <= band_max)
        masked_fft = np.abs(fft_data[mask])
        if len(masked_fft) == 0:
            return None, None
        
        peak_idx = np.argmax(masked_fft)
        peak_freq = freqs[mask][peak_idx]
        peak_power = 20 * np.log10(masked_fft[peak_idx] + 1e-10)
        
        return peak_freq, peak_power

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.data_queue.put(indata[:, 0])

    def stream_audio(self, plot=False):
        if plot:
            fig, line_time, line_freq, peak_point = self._setup_plot()
        
        try:
            with sd.InputStream(callback=self.audio_callback, 
                              channels=1, 
                              samplerate=self.sample_rate):
                print("Streaming audio... Press Ctrl+C to stop.")
                while True:
                    self._update_stream(plot, fig, line_time, line_freq, peak_point if plot else None)
                    if plot:
                        plt.pause(0.01)
        except KeyboardInterrupt:
            print("Stopped streaming.")

    def _update_stream(self, plot, fig=None, line_time=None, line_freq=None, peak_point=None):
        try:
            data = self.data_queue.get_nowait()
            if len(data) != self.buffer_size:
                data = np.resize(data, self.buffer_size)
            
            freqs, fft_mag, fft_data = self.process_audio_data(data)
            peak_freq, peak_power = self.get_range_peak(fft_data, freqs, 
                                                      self.freq_min, self.freq_max)
            
            if plot:
                self._update_plots(data, freqs, fft_mag, peak_freq, peak_power,
                                 fig, line_time, line_freq, peak_point)
            
            return peak_freq, peak_power
            
        except Empty:
            return None, None

    def _setup_plot(self):
        global ax1, ax2
        plt.ion()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Time domain plot
        x = np.arange(self.buffer_size) / self.sample_rate
        line_time, = ax1.plot(x, np.zeros(self.buffer_size), '-')
        ax1.set_ylim(-1, 1)
        ax1.set_xlim(0, self.duration)
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Amplitude")
        ax1.set_title("Real-Time Audio Signal")
        
        # Frequency domain plot - limit to 10000 Hz
        freqs = np.fft.fftfreq(self.buffer_size, 1/self.sample_rate)
        freq_mask = (freqs >= 0) & (freqs <= self.max_freq_collected)  # New mask for frequencies
        line_freq, = ax2.plot(freqs[freq_mask], np.zeros(np.sum(freq_mask)), '-')
        peak_point, = ax2.plot([], [], 'ro', markersize=10, label='Peak')
        ax2.set_xlim(0, self.max_freq_collected)
        ax2.set_ylim(0, 60)
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Magnitude (dB)")
        ax2.set_title("Real-Time FFT")
        ax2.legend()
        
        plt.tight_layout()
        return fig, line_time, line_freq, peak_point

    def _update_plots(self, data, freqs, fft_mag, peak_freq, peak_power,
                     fig, line_time, line_freq, peak_point):
        line_time.set_ydata(data)
        line_freq.set_ydata(fft_mag)
        peak_point.set_data([peak_freq], [peak_power])
        ax2.set_title(f"Real-Time FFT")
        fig.canvas.draw_idle()
        fig.canvas.flush_events()

if __name__ == "__main__":
    processor = AudioProcessor()
    processor.stream_audio(plot=True)