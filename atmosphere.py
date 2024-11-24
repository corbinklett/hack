import numpy as np
import matplotlib.pyplot as plt

# Function to calculate air absorption in dB/km
def air_absorption(frequency, temperature, humidity):
    # Parameters for absorption coefficient based on empirical data
    alpha_0 = 0.0001  # Base absorption coefficient in dB/m/Hz^2 at reference conditions

    # Convert frequency to kHz for calculations
    frequency_khz = frequency / 1000.0

    # Calculate the air absorption coefficient
    alpha = alpha_0 * (frequency_khz ** 2) * (1 + 0.001 * (temperature - 20)) * (1 + 0.004 * humidity)
    # Convert to dB/km
    absorption_db_km = alpha * 1000
    return absorption_db_km

# Function to calculate total sound attenuation (air absorption + inverse square law)
def total_attenuation(frequency, distance, temperature, humidity):
    # Air absorption component
    air_absorption_loss = air_absorption(frequency, temperature, humidity) * distance / 1000  # Convert distance to km
    
    # Inverse square law component
    inverse_square_loss = 20 * np.log10(distance)
    
    # Total attenuation
    total_loss = air_absorption_loss + inverse_square_loss
    return total_loss

# Environmental variables for modeling
frequencies = np.arange(100, 20000, 100)  # Frequency range from 100 Hz to 20 kHz
distance = 1000  # Distance in meters (1 km)
temperature = 20  # Constant temperature of 20°C
humidity_levels = [20, 40, 60, 80]  # Different humidity levels to analyze

# Plotting the results
plt.figure(figsize=(12, 8))
for humidity in humidity_levels:
    attenuation_values = [total_attenuation(freq, distance, temperature, humidity) for freq in frequencies]
    plt.plot(frequencies, attenuation_values, label=f'Humidity {humidity}%')

plt.title('Total Sound Attenuation as a Function of Frequency and Humidity')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Total Attenuation (dB)')
plt.xscale('log')
plt.grid(True, which='both', linestyle='--')
plt.legend()
plt.show()