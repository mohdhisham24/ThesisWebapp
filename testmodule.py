import RPi.GPIO as GPIO
import time

# Set up GPIO using BOARD numbering
GPIO.setmode(GPIO.BOARD)

# Define pin numbers (physical pin numbers)
CLK = 3  # GPIO 2 is physical pin 3
DT = 5   # GPIO 3 is physical pin 5
SW = 7   # GPIO 4 is physical pin 7

# Set up pins as inputs
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

clkLastState = GPIO.input(CLK)

try:
    while True:
        clkState = GPIO.input(CLK)
        dtState = GPIO.input(DT)
        swState = GPIO.input(SW)
        
        if clkState != clkLastState:
            if dtState != clkState:
                print("Clockwise")
            else:
                print("Counterclockwise")
        
        if swState == GPIO.LOW:
            print("Button pressed")
        
        clkLastState = clkState
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up")