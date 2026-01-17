"""
A mock implementation of the RPi.GPIO library for running on non-Pi systems.
This allows for development and testing on a standard PC without needing
the actual GPIO hardware.
"""

# Mock constants to match the RPi.GPIO library's API
BCM = 11
IN = 1
OUT = 0
PUD_DOWN = 21
PUD_UP = 22

def setmode(mode):
    """Mock for RPi.GPIO.setmode. Prints the mode being set."""
    print(f"GPIO mock: setmode({mode})")

def setup(pin, mode, pull_up_down=None):
    """Mock for RPi.GPIO.setup. Prints the pin and mode configuration."""
    print(f"GPIO mock: setup({pin}, {mode}, pull_up_down={pull_up_down})")

def input(pin):
    """
    Mock for RPi.GPIO.input. 
    
    Args:
        pin: The pin to read from (ignored in mock).

    Returns:
        Always returns 0 (low), simulating no button presses.
    """
    return 0

def output(pin, value):
    """
    Mock for RPi.GPIO.output. Does nothing.
    
    Args:
        pin: The pin to write to (ignored).
        value: The value to write (ignored).
    """
    pass

def cleanup():
    """Mock for RPi.GPIO.cleanup. Prints a cleanup message."""
    print("GPIO mock: cleanup()")

def setwarnings(flag):
    """Mock for RPi.GPIO.setwarnings. Prints the flag being set."""
    print(f"GPIO mock: setwarnings({flag})")
