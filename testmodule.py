from gpiozero import RotaryEncoder, Button
from signal import pause
import time

# Define pin numbers (BCM numbering)
CLK = 13
DT = 18
SW = 12

# Create a RotaryEncoder instance
rotor = RotaryEncoder(CLK, DT)
button = Button(SW, pull_up=True)

def rotated():
    print(f"Rotated: {'Clockwise' if rotor.value > 0 else 'Counterclockwise'}")
    print(f"Steps: {rotor.steps}")

def button_pressed():
    print("Button pressed")

# Set up event handlers
rotor.when_rotated = rotated
button.when_pressed = button_pressed

print("Rotary Encoder Test. Press CTRL+C to exit.")

try:
    while True:
        # This loop keeps the script running
        # All events are handled by the callbacks
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    # gpiozero automatically cleans up GPIO resources
    print("GPIO cleaned up")





