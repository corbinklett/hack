import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

def triangulate_target(ground_stations):
    """
    Triangulate the position of the target based on a list of ground stations.
    Each ground station is a tuple of (x, y, distance), where (x, y) is the
    position of the station and 'distance' is the distance from the target.
    
    Arguments:
    ground_stations -- list of tuples [(x1, y1, d1), (x2, y2, d2), ..., (xn, yn, dn)]
    
    Returns:
    A tuple (x_target, y_target) representing the best guess for the target's position.
    """
    
    # Function to compute the residuals (sum of squared differences between actual and calculated distances)
    def residuals(params):
        x_t, y_t = params
        residuals_sum = 0
        for (x_i, y_i, d_i) in ground_stations:
            # Compute the distance from the estimated target to each ground station
            calculated_distance = np.sqrt((x_t - x_i)**2 + (y_t - y_i)**2)
            # The residual is the difference between the actual distance and the calculated distance
            residuals_sum += (calculated_distance - d_i)**2
        return residuals_sum
    
    # Initial guess for the target's position (using the centroid of the stations as a starting point)
    initial_guess = np.mean([station[:2] for station in ground_stations], axis=0)
    
    # Minimize the residuals to find the best estimate of the target position
    result = minimize(residuals, initial_guess, method='Nelder-Mead')
    
    if result.success:
        x_target, y_target = result.x
    else:
        raise ValueError("Triangulation failed to converge.")

    return x_target, y_target



# Example usage:
if __name__ == "__main__":
    # On the receiver computer, run:
        # Example usage:
    ground_stations = [
        (0, 3, 5),  # Station at (0, 0) with a distance of 5 units
        (0, -3, 8),  # Station at (4, 0) with a distance of 5 units
        (-1, 0, 6)   # Station at (2, 4) with a distance of 4 units
    ]
    
    target_position = triangulate_target(ground_stations)
    x_target = target_position[0]
    y_target = target_position[1]
    print(f"The estimated position of the target is: {target_position}")
    
     # Plotting the circles and target position
    plt.figure(figsize=(8, 8))
    ax = plt.gca()
    
    # Plot each ground station and its corresponding circle
    for (x_i, y_i, d_i) in ground_stations:
        circle = plt.Circle((x_i, y_i), d_i, color='blue', fill=False, linestyle='--', label=f'Station ({x_i}, {y_i})')
        ax.add_patch(circle)
        plt.plot(x_i, y_i, 'bo')  # Plot the station as blue dots
    
    # Plot the estimated target position
    plt.plot(x_target, y_target, 'rx', label=f'Estimated Target ({x_target:.2f}, {y_target:.2f})', markersize=10)
    
    # Labels and title
    plt.title('Triangulation of Target Position')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid(True)
    plt.show()
    
   
    pass