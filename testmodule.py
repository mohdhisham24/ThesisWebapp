import lgpio
import time

# Set up GPIO using lgpio
h = lgpio.gpiochip_open(0)

# Define pin numbers (BCM numbering)
CLK = 2
DT = 3
SW = 4

# Set up pins as inputs
lgpio.gpio_claim_input(h, CLK)
lgpio.gpio_claim_input(h, DT)
lgpio.gpio_claim_input(h, SW)

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