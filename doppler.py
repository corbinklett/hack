import numpy as np
from scipy.optimize import least_squares

# Constants
c = 343  # Speed of sound (m/s)

# Inputs
frequencies = [1000, 1020, 980]  # Observed frequencies at microphones (Hz)
mic_positions = [(0, 0), (1, 0), (0, 1)]  # Microphone positions (x, y)

# Normalize frequencies to remove f_s
f_ratios = [frequencies[i] / frequencies[0] for i in range(1, len(frequencies))]

# Define the residual function
def residuals(params):
    x_d, y_d, h, v_x, v_y, v_h = params
    res = []
    
    for i in range(1, len(mic_positions)):
        # Positions
        x_i, y_i = mic_positions[i]
        x_j, y_j = mic_positions[0]
        
        # Distances
        r_i = np.sqrt((x_d - x_i)**2 + (y_d - y_i)**2 + h**2)
        r_j = np.sqrt((x_d - x_j)**2 + (y_d - y_j)**2 + h**2)
        
        # Relative velocities
        v_par_i = (v_x * (x_d - x_i) + v_y * (y_d - y_i) + v_h * h) / r_i
        v_par_j = (v_x * (x_d - x_j) + v_y * (y_d - y_j) + v_h * h) / r_j
        
        # Doppler shift ratios
        doppler_ratio = (c - v_par_j) / (c - v_par_i)

        print(i, doppler_ratio)
        # Residual: difference between calculated and observed ratios
        res.append(doppler_ratio - f_ratios[i - 1])
    
    return res

# Initial guesses for optimization
initial_guess = [0.5, 0.5, 1.0, 0.0, 0.0, 0.0]

# Solve the system of equations
result = least_squares(residuals, initial_guess)

# Output the results
x_d, y_d, h, v_x, v_y, v_h = result.x
print(f"Drone position: ({x_d:.2f}, {y_d:.2f}, {h:.2f})")
print(f"Drone velocity: ({v_x:.2f}, {v_y:.2f}, {v_h:.2f})")
