# Defense Tech Hackathon at the USS Hornet

https://www.defense-tech-hackathon.com/

## Acoustic Drone Detection System

This system uses multiple ground stations to detect and triangulate the position of drones using acoustic signals. Each ground station captures audio and processes the frequency spectrum to identify drone signatures.

### Running Ground Stations

You can run ground stations in either sender or receiver mode:

#### Receiver Station (Main Hub)

```python
station = GroundStation('receiver',
host='0.0.0.0', # Listen on all interfaces
port=58392,
plot_enabled=True, # Enable real-time plotting
name="Main",
low_cutoff_Hz=500, # Minimum frequency to detect
thresh_dB=30) # Detection threshold
station.start()
```

#### Sender Station (Remote Sensor)

```python
station = GroundStation('sender',
host='10....', # IP address of receiver
port=58392,
location=(4,0), # X,Y coordinates of this station
name='sensor1',
low_cutoff_Hz=500,
thresh_dB=50)
station.start()
```

### Real-time Audio Analysis

To visualize raw audio waveforms and frequency spectrums in real-time:

```python
python audio.py
```

This will display:
- Time domain signal amplitude
- Total power in dB
- Real-time FFT frequency spectrum
- Peak frequency detection

### Requirements

- Python 3.7+
- sounddevice
- numpy
- matplotlib
- scipy