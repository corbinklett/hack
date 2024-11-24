import numpy as np
from scipy.optimize import minimize

def triangulate_target(circles):
    """
    Find the point closest to the intersection of n circles.
    
    Parameters:
        circles (list): Each element is a tuple ((x, y), r) where (x, y) is the center
                       and r is the radius.
    Returns:
        tuple: Coordinates (x, y) of the closest point to the intersection.
    """
    # Convert input format to list of (x, y, r)
    circles = [(center[0], center[1], radius) for center, radius in circles]
    
    # Objective function
    def objective(point):
        x, y = point
        residuals = [
            (np.sqrt((x - cx)**2 + (y - cy)**2) - r)**2
            for cx, cy, r in circles
        ]
        return sum(residuals)

    # Initial guess: centroid of circle centers
    x0 = np.mean([c[0] for c in circles])
    y0 = np.mean([c[1] for c in circles])

    # Minimize the objective function
    result = minimize(objective, (x0, y0), method='BFGS')

    if result.success:
        return result.x
    else:
        raise ValueError("Optimization failed!")
    
import matplotlib.pyplot as plt

def plot_circles_and_point(circles, point):
    fig, ax = plt.subplots()
    for cx, cy, r in circles:
        circle = plt.Circle((cx, cy), r, fill=False, linestyle='--')
        ax.add_artist(circle)
    ax.plot(point[0], point[1], 'ro', label='Closest Point')
    ax.set_xlim(-10, 20)
    ax.set_ylim(-10, 20)
    ax.set_aspect('equal', 'box')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    # Test cases
    test_cases = [
        # Original test case - roughly equilateral triangle arrangement
        [((0, 0), 5), ((10, 0), 5), ((5, 8), 5)],
                
        # Two circles - barely touching
        [((0, 0), 3), ((5, 0), 3)],
        
        # Overlapping circles with different radii
        [((0, 0), 3), ((2, 0), 4), ((1, 2), 2)],
        
        # Four circles arrangement
        [((0, 0), 4), ((5, 0), 4), ((0, 5), 4), ((5, 5), 4)],
        
        # Circles with very different radii
        [((0, 0), 10), ((8, 0), 3), ((4, 6), 5)],
        
        # Circles in a line
        [((0, 0), 3), ((5, 0), 2), ((10, 0), 4)]
    ]
    
    # Run tests for each case
    for i, circles in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        try:
            closest_point = triangulate_target(circles)
            print(f"Closest point to intersection: {closest_point}")
            
            # Visualization
            plot_circles_and_point([(c[0][0], c[0][1], c[1]) for c in circles], closest_point)
        except Exception as e:
            print(f"Error processing test case: {str(e)}")