import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import math
import random

def calculate_Doppler(GS_x, GS_y, drone_x, drone_y, speed_x, speed_y):
    drone_pos = np.array([drone_x, drone_y])
    GS_pos = np.array([GS_x, GS_y])
    r_i = GS_pos - drone_pos
    drone_speed = [speed_x, speed_y]
    speed_towards_GS = np.dot(drone_speed, r_i)/ np.linalg.norm(r_i)
    
    frequency = 8000 * (343/ (343-speed_towards_GS))
    
    return(frequency)

def calculate_Audio(GS_x, GS_y, drone_x, drone_y):
    distance = math.sqrt((drone_x - GS_x)**2 + (drone_y - GS_y)**2)

    Audio_dataset = 'Audio_dataset.csv'  # Replace with the path to your CSV file
    Audio_df = pd.read_csv(Audio_dataset)
    Audio_df = Audio_df.sort_values(by='X')
    interpolator = interp1d(Audio_df['X'], Audio_df['Y'], kind='linear', fill_value='extrapolate')
    return(interpolator(distance))

def calculate_EMI(GS_x, GS_y, drone_x, drone_y):
    distance = math.sqrt((drone_x - GS_x)**2 + (drone_y - GS_y)**2)

    EMI_dataset = 'EMI_dataset.csv'  # Replace with the path to your CSV file
    EMI_df = pd.read_csv(EMI_dataset)
    EMI_df = EMI_df.sort_values(by='X')
    interpolator = interp1d(EMI_df['X'], EMI_df['Y'], kind='linear', fill_value='extrapolate')
    return(interpolator(distance))

def calculate_trajectory(x_start, y_start, x_end, y_end, speed, timestep):
    # Calculate the total distance between the start and end points
    distance = np.sqrt((x_end - x_start)**2 + (y_end - y_start)**2)
    
    # Calculate the total time required to travel this distance at the given speed
    total_time = distance / speed
    
    # Calculate the number of timesteps needed
    num_steps = int(total_time / timestep)
    
    # Initialize arrays for storing the trajectory
    x_coords = []
    y_coords = []
    
    # Calculate the direction of movement (unit vector)
    dx = (x_end - x_start) / distance
    dy = (y_end - y_start) / distance
    
    # Calculate the position at each timestep
    for step in range(num_steps + 1):
        # Calculate the current position
        x_current = x_start + dx * speed * step * timestep
        y_current = y_start + dy * speed * step * timestep
        
        # Append to the coordinate lists
        x_coords.append(int(x_current))
        y_coords.append(int(y_current))
    
    # Return the trajectory as a matrix of x and y coordinates
    return np.array([x_coords, y_coords]).T

# Example usage:
if __name__ == "__main__":    
    x_start = 1000
    y_start = random.randint(-50, 50) #unit m
    x_end = 0
    y_end = random.randint(-50, 50) #unit m
    speed = random.randint(20, 60) #unit m/s
    timestep = 0.5  # seconds
    
    trajectory = calculate_trajectory(x_start, y_start, x_end, y_end, speed, timestep)
    
    distance = np.sqrt((x_end - x_start)**2 + (y_end - y_start)**2)
    x_speed = speed*(x_start/distance)
    y_speed = speed*((y_end-y_start)/distance)    
    
    #print("Trajectory (x, y):")
    #print(trajectory)
    
    for point in trajectory:
        # Unpack the row into x and y (since there are two columns)
        x, y = point
        # Call the function with the unpacked values
        EMI_val = calculate_EMI(x, y, 0, 0)
        Audio_val = calculate_Audio(x, y, 0, 0)
        Doppler_val = calculate_Doppler(x, y, 0, 0, x_speed, y_speed)
        print(f"EMI: {EMI_val}")
        print(f"Audio: {Audio_val}")
        print(f"Doppler: {Doppler_val}\n")
    pass