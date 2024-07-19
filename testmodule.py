import lgpio
import time

# Open a handle to the GPIO chip
h = lgpio.gpiochip_open(0)

# Define pin numbers (BCM numbering)
CLK = 2
DT = 4
SW = 12

def claim_pin(h, pin):
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            lgpio.gpio_claim_input(h, pin)
            print(f"Successfully claimed pin {pin}")
            return True
        except lgpio.error as e:
            if "GPIO busy" in str(e):
                print(f"Attempt {attempt + 1}: GPIO {pin} is busy. Waiting and trying again...")
                time.sleep(1)
            else:
                print(f"Unexpected error claiming GPIO {pin}: {e}")
                return False
    print(f"Failed to claim GPIO {pin} after {max_attempts} attempts")
    return False

# Set up pins as inputs
if not all(claim_pin(h, pin) for pin in [CLK, DT, SW]):
    print("Failed to claim all required pins. Exiting.")
    lgpio.gpiochip_close(h)
    exit(1)

clkLastState = lgpio.gpio_read(h, CLK)

try:
    while True:
        clkState = lgpio.gpio_read(h, CLK)
        dtState = lgpio.gpio_read(h, DT)
        swState = lgpio.gpio_read(h, SW)
        
        if clkState != clkLastState:
            if dtState != clkState:
                print("Clockwise")
            else:
                print("Counterclockwise")
        
        if swState == 0:
            print("Button pressed")
        
        clkLastState = clkState
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    lgpio.gpiochip_close(h)
    print("GPIO cleaned up")
