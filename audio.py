import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from queue import Queue, Empty
from scipy.fft import fft
import pandas as pd
from filter import match_signal_shape, read_and_process_data
best_peak = 0
peak_freq = 0

class AudioProcessor:
    def __init__(self, sample_rate=44100, duration=0.1, freq_min=500, freq_max=10000, max_freq_collected=10000):
        self.sample_rate = sample_rate
        self.duration = duration
        self.buffer_size = int(sample_rate * duration)
        self.freq_min = freq_min
        self.freq_max = freq_max
        self.max_freq_collected = max_freq_collected
        self.data_queue = Queue()
        
        # Add reference data loading
        self.df, _, self.freq_mask, _ = self.load_reference_data()

    def load_reference_data(self):
        """Load and process reference data"""
        try:
            return read_and_process_data('fft_amplitudes_1.csv')
        except FileNotFoundError:
            print("Warning: Reference data file not found. Matched signal overlay disabled.")
            return None, None, None, None

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
        global best_peak, peak_freq  # Declare globals at start of function
        
        mask = (freqs >= band_min) & (freqs <= band_max)
        masked_fft = np.abs(fft_data[mask])
        if len(masked_fft) == 0:
            return None, None, None
        
        peak_idx = np.argmax(masked_fft)
        peak_freq = freqs[mask][peak_idx]
        peak_power = 20 * np.log10(masked_fft[peak_idx] + 1e-10)

        # Calculate matched signal and correlation
        # if self.df is not None:
        #     matched_signal, correlation = match_signal_shape(np.abs(fft_data), self.df, 
        #                                                   self.freq_mask, reference_distance=2)
        #     # Calculate total power from matched signal within the frequency band
        #     matched_signal_masked = matched_signal #[mask]
        #     total_power = 20 * np.log10(np.sum(matched_signal_masked) + 1e-10)
        # else:
        #     # Fallback to original calculation if no reference data
        total_power = 20 * np.log10(np.sum(masked_fft) + 1e-10)

        if peak_power > best_peak and peak_freq > self.freq_min:
            best_peak = peak_power
            peak_freq = peak_freq
            print(f"New best peak: {best_peak} at {peak_freq} Hz")
        
        return peak_freq, peak_power, total_power

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.data_queue.put(indata[:, 0])

    def stream_audio(self, plot=False):
        if plot:
            fig, line_time, line_freq, peak_point, line_db, matched_line = self._setup_plot()
        
        try:
            with sd.InputStream(callback=self.audio_callback, 
                              channels=1, 
                              samplerate=self.sample_rate):
                print("Streaming audio... Press Ctrl+C to stop.")
                while True:
                    self._update_stream(plot, fig, line_time, line_freq, peak_point if plot else None, line_db if plot else None, matched_line if plot else None)
                    if plot:
                        plt.pause(0.01)
        except KeyboardInterrupt:
            print("Stopped streaming.")

    def _update_stream(self, plot, fig=None, line_time=None, line_freq=None, 
                      peak_point=None, line_db=None, matched_line=None):
        try:
            data = self.data_queue.get_nowait()
            if len(data) != self.buffer_size:
                data = np.resize(data, self.buffer_size)
            
            freqs, fft_mag, fft_data = self.process_audio_data(data)
            peak_freq, peak_power, total_power = self.get_range_peak(fft_data, freqs, 
                                                      self.freq_min, self.freq_max)
            
            if plot:
                self._update_plots(data, freqs, fft_mag, peak_freq, peak_power, total_power,
                                 fig, line_time, line_freq, peak_point, line_db, matched_line)
            
            return peak_freq, peak_power, total_power
            
        except Empty:
            return None, None, None

    def _setup_plot(self):
        global ax1, ax2
        plt.ion()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Time domain plot with two y-axes
        x = np.arange(self.buffer_size) / self.sample_rate
        line_time, = ax1.plot(x, np.zeros(self.buffer_size), '-', color='blue', 
                             label='Amplitude', alpha=0.5)  # Made slightly transparent
        ax1.set_ylim(-1, 1)
        ax1.set_xlim(0, self.duration)
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Amplitude", color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        # Add secondary y-axis for decibels
        ax1_db = ax1.twinx()
        line_db, = ax1_db.plot(x, np.zeros(self.buffer_size), '-', color='red', 
                              label=f'Total Power ({self.freq_min}-{self.freq_max} Hz)',
                              linewidth=2.0,  # Made line thicker
                              zorder=10)      # Ensure it's on top
        ax1_db.set_ylabel('Total Power (dB)', color='red')
        ax1_db.tick_params(axis='y', labelcolor='red')
        ax1_db.set_ylim(0, 100)  # Adjust these limits as needed
        
        # Add legends for both axes
        lines = line_time, line_db
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper right')
        
        ax1.set_title("Real-Time Audio Signal and Power")
        
        # Frequency domain plot - limit to 10000 Hz
        freqs = np.fft.fftfreq(self.buffer_size, 1/self.sample_rate)
        freq_mask = (freqs >= 0) & (freqs <= self.max_freq_collected)
        line_freq, = ax2.plot(freqs[freq_mask], np.zeros(np.sum(freq_mask)), '-', label='Current Signal')
        matched_line, = ax2.plot(freqs[freq_mask], np.zeros(np.sum(freq_mask)), '--', 
                                alpha=0.7, label='Matched Reference', color='green')
        peak_point, = ax2.plot([], [], 'ro', markersize=10, label='Peak')
        ax2.set_xlim(0, self.max_freq_collected)
        ax2.set_ylim(0, 60)
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Magnitude (dB)")
        ax2.set_title("Real-Time FFT")
        ax2.legend()
        
        plt.tight_layout()
        return fig, line_time, line_freq, peak_point, line_db, matched_line

    def _update_plots(self, data, freqs, fft_mag, peak_freq, peak_power, total_power,
                     fig, line_time, line_freq, peak_point, line_db, matched_line):
        line_time.set_ydata(data)
        line_freq.set_ydata(fft_mag)
        peak_point.set_data([peak_freq], [peak_power])
        
        # Update matched signal if reference data is available
        if self.df is not None:
            matched_signal, correlation = match_signal_shape(np.power(10, fft_mag/20), self.df, 
                                                 self.freq_mask, reference_distance=2)
            
            # Make sure matched_signal matches the frequency data length
            if len(matched_signal) != len(freqs):
                matched_signal = np.interp(
                    np.linspace(0, 1, len(freqs)),
                    np.linspace(0, 1, len(matched_signal)),
                    matched_signal
                )
            matched_line.set_ydata(20 * np.log10(matched_signal + 1e-10))
        
        # Ensure db_data matches the time domain data length
        db_data = np.full(len(data), total_power if total_power is not None else 0)
        line_db.set_ydata(db_data)
        
        fig.canvas.draw_idle()
        fig.canvas.flush_events()

if __name__ == "__main__":
    processor = AudioProcessor()
    processor.stream_audio(plot=True)