import queue
import threading
import platform
import time
import pygame
from config import KEY_EVENT_MAP
from events import Events

# Determine if the code is running on a Raspberry Pi
IS_PI = platform.machine().startswith("arm")

# Use the actual GPIO library on a Pi, otherwise use a mock
if IS_PI:
    import RPi.GPIO as GPIO
else:
    import gpio_mock as GPIO

class Button:
    """
    Represents a physical button connected to a GPIO pin.
    Triggers a specific event when pressed.
    """
    def __init__(self, pin, event, event_manager):
        """
        Initializes a Button.

        Args:
            pin: The GPIO pin number.
            event: The event to trigger when the button is pressed.
            event_manager: The EventManager instance to post events to.
        """
        self.event_manager = event_manager
        self.pin = pin
        self.event = event
        self.is_pressed = False

    def handle_state(self, is_high):
        """
        Handles the button's state change. Triggers an event on the rising edge.

        Args:
            is_high: True if the GPIO signal is high, False otherwise.
        """
        if is_high and not self.is_pressed:
            self.is_pressed = True
            self._trigger_event()
        elif not is_high:
            self.is_pressed = False

    def _trigger_event(self):
        """Puts the button's designated event onto the event queue."""
        print(f"Event: {self.event}")
        self.event_manager.event_queue.put(self.event)

class EventManager:
    """
    Manages all user input, from GPIO buttons and keyboard, and queues events.
    """
    def __init__(self):
        """Initializes the EventManager, setting up the event queue and buttons."""
        self.event_queue = queue.Queue()
        self.running = True
        self.resize_size = None  # Updated when a VIDEORESIZE event occurs
        
        # Maps GPIO pins to their corresponding events
        self.button_map = {
            1: Events.BUTTON_LEFT,
            12: Events.BUTTON_UP,
            14: Events.BUTTON_RIGHT,
            16: Events.BUTTON_DOWN,
            19: Events.BUTTON_ENTER,
            7: Events.BUTTON_FLAG,
            15: Events.QUIT
        }

        # Create Button instances from the map
        self.buttons = [Button(pin, event, self) for pin, event in self.button_map.items()]
        self.gpio_thread = None

    def start(self):
        """
        Starts the input listeners.
        Initializes GPIO on a Raspberry Pi and starts the listener thread.
        """
        if IS_PI:
            GPIO.setmode(GPIO.BCM)
            for btn in self.buttons:
                GPIO.setup(btn.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            
            self.gpio_thread = threading.Thread(target=self._gpio_listener, daemon=True)
            self.gpio_thread.start()

    def stop(self):
        """Stops the input listeners and joins any running threads."""
        self.running = False
        self.event_queue.put(Events.QUIT) # Ensure the main loop exits
        
        # Join the GPIO handling thread if it exists
        if self.gpio_thread and self.gpio_thread.is_alive():
            try:
                self.gpio_thread.join()
            except RuntimeError:
                pass # Thread may not have been started

    def get_events(self):
        """
        Retrieves all events currently in the queue.

        Returns:
            A list of all events that have occurred since the last call.
        """
        events = []
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                if event is Events.QUIT:
                    self.running = False
                events.append(event)
            except queue.Empty:
                break
        return events
    
    def process_pygame_events(self):
        """
        Processes Pygame events (like keyboard input and window close)
        and adds them to the internal event queue.
        """
        for py_event in pygame.event.get():
            if py_event.type == pygame.QUIT:
                self.event_queue.put(Events.QUIT)
            elif py_event.type == pygame.KEYDOWN:
                if py_event.key in KEY_EVENT_MAP:
                    self.event_queue.put(KEY_EVENT_MAP[py_event.key])
            elif py_event.type == pygame.VIDEORESIZE:
                # Store the new size so main loop can adjust surfaces
                self.resize_size = (py_event.w, py_event.h)

    def _gpio_listener(self):
        """
        Continuously listens for GPIO pin state changes and updates buttons.
        This method runs in a separate thread.
        """
        while self.running:
            for btn in self.buttons:
                is_high = (GPIO.input(btn.pin) != 0)
                btn.handle_state(is_high)
            time.sleep(0.02) # Small delay to prevent busy-looping







