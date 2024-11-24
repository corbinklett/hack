import matplotlib.pyplot as plt
import matplotlib.animation as animation
from ground import GroundStation

def update_stream(station):
    # This function updates the data from sender_data
    # You can add any additional processing here if needed
    return station.sender_data

def plot_real_time_frequencies(station):
    fig, ax = plt.subplots()
    lines = {}

    def init():
        ax.set_xlim(0, len(station.sender_data))
        ax.set_ylim(0, max(freq for freq, _ in station.sender_data.values()) + 10)
        ax.set_xlabel('Microphone')
        ax.set_ylabel('Frequency (Hz)')
        ax.set_title('Real-time Frequencies from Microphones')
        for i, source in enumerate(station.sender_data.keys()):
            print(source)
            line, = ax.plot([], [], label=source)
            lines[source] = line
        ax.legend()
        
        return lines.values()

    def update(frame):
        sender_data = update_stream(station)
        for i, (source, (freq, _)) in enumerate(sender_data.items()):
            lines[source].set_data([i], [freq])
        return lines.values()
    
    init()
    
    ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=1000)
    plt.show()

    

if __name__ == "__main__":
    # station = GroundStation('receiver', host='0.0.0.0', port=58394)
    # station.start()
    plot_real_time_frequencies(station)