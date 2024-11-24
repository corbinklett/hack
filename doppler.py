import numpy as np
import numpy.linalg
import scipy
# Plot 3D drone location and velocity vector
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

def get_drone(observed_freq, ground_stations):

    # Constants
    c = 343  # Speed of sound (m/s)
    
    # Inputs
    frequencies = observed_freq  # Observed frequencies at microphones (Hz)
    mic_positions = ground_stations  # Microphone positions (x, y)
    
    # Normalize frequencies to remove f_s
    f_ratios = [frequencies[i] / frequencies[0] for i in range(1, len(frequencies))]
    
    # Define the residual function
    def residuals(params):
        x_d, y_d, h, v_x, v_y, v_h = params
        res = []
        
        for i in range(1, len(mic_positions)-1):
            # Positions
            x_i, y_i, z_i = mic_positions[i]
            x_j, y_j, z_j = mic_positions[0]
            
            # Distances
            r_i = np.sqrt((x_d - x_i)**2 + (y_d - y_i)**2 + h**2)
            r_j = np.sqrt((x_d - x_j)**2 + (y_d - y_j)**2 + h**2)
            
            # Relative velocities
            v_par_i = -(v_x * (x_d - x_i) + v_y * (y_d - y_i) + v_h * h) / r_i
            v_par_j = -(v_x * (x_d - x_j) + v_y * (y_d - y_j) + v_h * h) / r_j
            
            # Doppler shift ratios
            doppler_ratio = (c - v_par_j) / (c - v_par_i)
    
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
    return result.x

def doppler_shift(drone_position, drone_velocity, microphone_positions, source_frequency):
    '''spoofs fake dopper shift data'''
    c = 343  # Speed of sound (m/s)
    frequencies = []
    
    for mic_pos in microphone_positions:
        # Compute the vector from the drone to the microphone
        r_i = mic_pos - drone_position  # Ignore z for the microphone (ground level)
        # r_i = np.append(r_i, -drone_position[2])  # Add height difference (h) to the z-component
        
        # Compute the relative velocity component along the line of sight
        v_parallel_i = np.dot(drone_velocity, r_i) / np.linalg.norm(r_i)
        
        # Compute the observed frequency at the microphone using the Doppler effect
        observed_frequency = source_frequency * (c / (c - v_parallel_i))
        frequencies.append(observed_frequency)
    
    return frequencies

if __name__ == "__main__":
    ground_stations=[[0, 0, 0], [5, 0, 0], [0, 5, 0], [0, 10, 0], [10,0,0], [10,10,0], [10, 5, 0], [5, 10, 0]]
    d_state_true = [5, 5, 5, 1, 0, 0] # [x, y, z, vz, vy, vz] position and velocity vector of drone 
    d_pos_true = d_state_true[:3]
    d_vel_true = d_state_true[3:] #m/s
    # Inputs
    drone_position = np.array(d_pos_true)  # Position of the drone (x_d, y_d, h)
    drone_velocity = np.array(d_vel_true)  # Velocity of the drone (v_x, v_y, v_h)
    microphone_positions = np.array(ground_stations)  # Positions of microphones
    source_frequency = 6000  # Source frequency emitted by the drone

    observed_frequencies = doppler_shift(drone_position, drone_velocity, microphone_positions, source_frequency)

    drone_state_mes = get_drone(observed_frequencies, ground_stations)