import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file
df = pd.read_csv('fft_amplitudes_1.csv')

# Get frequencies from column names (skip 'Distance' column)
frequencies = [float(col.replace(' Hz', '')) for col in df.columns[1:]]

# Create a mask for frequencies in range 0-10000 Hz
freq_mask = [f <= 10000 for f in frequencies]
filtered_frequencies = [f for f, mask in zip(frequencies, freq_mask) if mask]

# Calculate total power for each distance
powers = []
for idx, row in df.iterrows():
    # Sum the squared amplitudes (using original values, not dB)
    # Skip the 'Distance' column by using row[1:]
    power = np.sum(row[1:].values[freq_mask]**2)
    powers.append(power)

# Create the first plot (your existing FFT plot)
plt.figure(figsize=(12, 6))
for idx, row in df.iterrows():
    distance = row['Distance']
    # Filter amplitudes to match frequency range and convert to dB
    amplitudes_db = 20 * np.log10(row[1:].values[freq_mask])
    plt.plot(filtered_frequencies, amplitudes_db, label=f'Distance={distance}')

plt.xlabel('Frequency (Hz)')
plt.ylabel('Amplitude (dB)')
plt.title('FFT Amplitudes vs Frequency (in dB) [0-10kHz]')
plt.grid(True)
plt.legend()

# Comment out or remove the log scale
# plt.xscale('log')

# Optional: Use log scale for y-axis if amplitudes vary widely
# plt.yscale('log')

plt.tight_layout()

# Create new plot for power vs distance
plt.figure(figsize=(12, 6))
plt.plot(df['Distance'], powers, 'b.-')
plt.xlabel('Distance')
plt.ylabel('Total Signal Power')
plt.title('Total Signal Power vs Distance')
plt.grid(True)
plt.tight_layout()
plt.show()
