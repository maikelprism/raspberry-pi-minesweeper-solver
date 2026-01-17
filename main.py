import pygame
from input import EventManager
from events import Events
from views import GameView, View, StartView, EmptyView
import sys
import platform
import config
from assets import AssetManager

# Determine if the code is running on a Raspberry Pi
IS_PI = platform.machine().startswith("arm")

class Application:
    """
    The main application class that orchestrates the entire game,
    including initialization, the main loop, and cleanup.
    """
    def __init__(self):
        """Initializes the application, loading assets and setting up the game context."""
        pygame.init()
        
        self.asset_manager = AssetManager()
        self.event_listener = EventManager()
        
        self._parse_args()
        self._init_display()
        # Use actual window size to initialize logical screen and backbuffer
        win_w, win_h = self.display_surface.get_size() if self.display_surface else (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        screen = Screen(win_w, win_h, config.COLOR_DEPTH)
        layer0 = pygame.Surface((screen.width, screen.height), depth=screen.color_depth)

        self.context = GameManager(
            screen,
            self.event_listener,
            layer0,
            self.language,
            self.minecount,
            self.asset_manager,
            ai_debug=getattr(self, "ai_debug", False),
        )
        self.context.initialize_game()

        # Set the initial view to the start screen
        view = StartView(self.context)
        self.context.set_view(view)
        
        self.running = True

    def _parse_args(self):
        """Parses command-line arguments.

        Usage: main.py <LANGUAGE> <MINECOUNT> [--ai-debug]
        LANGUAGE: EN | DE
        MINECOUNT: integer >= 10
        --ai-debug (optional): visualize AI solving/board generation.
        """
        if len(sys.argv) not in (3, 4):
            raise ValueError("Invalid Arguments, use: main.py <LANGUAGE> <MINECOUNT> [--ai-debug]")

        lang_arg = sys.argv[1].upper()
        if lang_arg in ["DE", "EN"]:
            self.language = lang_arg
        else:
            raise ValueError("Invalid language argument. Use DE or EN.")

        try:
            self.minecount = int(sys.argv[2])
            if self.minecount < 10:
                raise ValueError("Invalid minecount. Minecount cannot be smaller than 10.")
        except ValueError:
            raise ValueError("Invalid minecount. Must be an integer.")

        # Optional debug flag
        self.ai_debug = False
        if len(sys.argv) == 4:
            flag = sys.argv[3].lower()
            self.ai_debug = flag in ("--ai-debug", "--ai", "ai", "debug")

    def _init_display(self):
        """Initializes the display surface based on the platform."""
        if not IS_PI:
            flags = pygame.RESIZABLE
            # Clamp initial window size to fit on the desktop with a margin
            info = pygame.display.Info()
            margin_w, margin_h = 100, 100
            max_w = max(640, info.current_w - margin_w)
            max_h = max(480, info.current_h - margin_h)
            init_w = min(config.SCREEN_WIDTH, max_w)
            init_h = min(config.SCREEN_HEIGHT, max_h)

            self.display_surface = pygame.display.set_mode((init_w, init_h), flags)
            # Set a sensible minimum window size to keep UI readable
            try:
                pygame.display.set_window_min_size(800, 600)
            except Exception:
                pass
            pygame.display.set_caption(config.GAME_TITLE)
        else:
            self.display_surface = None

    def run(self):
        """Runs the main game loop."""
        while self.running:
            # Process all pending input events
            self.event_listener.process_pygame_events()

            # Handle window resize requested via EventManager
            if not IS_PI and getattr(self.event_listener, 'resize_size', None):
                new_w, new_h = self.event_listener.resize_size
                self.event_listener.resize_size = None
                # Recreate layer0 with new size while keeping logical game surface size
                self.context.screen.width = new_w
                self.context.screen.height = new_h
                self.context.layer0 = pygame.Surface((new_w, new_h), depth=self.context.screen.color_depth)
                # Update current view's reference to layer0 if present
                if hasattr(self.context.current_view, 'layer0'):
                    self.context.current_view.layer0 = self.context.layer0
                # Views may rely on offsets; force re-init of current view UI if it has that method
                if hasattr(self.context.current_view, '_init_ui_elements'):
                    try:
                        self.context.current_view._init_ui_elements()
                    except Exception as e:
                        print(f"Resize re-init failed: {e}")

            # Handle queued game events
            for event in self.event_listener.get_events():
                if event == Events.QUIT:
                    self.running = False
                else:
                    self.context.current_view.handle_event(event)

            # Update the current view's state and check for transitions
            next_view = self.context.current_view.update()
            if next_view is not self.context.current_view:
                self.context.set_view(next_view)

            # Draw the current view to the off-screen buffer
            self.context.current_view.draw()
            
            # Render the buffer to the screen
            render(self.context.layer0, self.display_surface)

        self.cleanup()

    def cleanup(self):
        """Performs cleanup operations before exiting the game."""
        print("Shutting down...")
        self.event_listener.stop()
        pygame.quit()
        sys.exit()

class Screen:
    """
    Represents the physical screen, holding its dimensions and color depth.
    """
    def __init__(self, width, height, color_depth):
        self.width = width
        self.height = height
        self.color_depth = color_depth

    def get_center(self):
        """Returns the center (x, y) coordinates of the screen."""
        return self.width // 2, self.height // 2

class GameManager:
    """
    A context object that holds shared game state and systems.
    It is passed to all views to provide access to common resources.
    """
    def __init__(self, screen, event_listener, layer0, 
                 language, minecount, asset_manager, ai_debug=False):
        self.screen = screen
        self.event_listener = event_listener
        self.layer0 = layer0 # The main off-screen drawing surface
        self.language = language
        self.minecount = minecount
        self.asset_manager = asset_manager
        self.current_view = None
        self.ai_debug = ai_debug

    def initialize_game(self):
        """Initializes Pygame subsystems and starts the event listener."""
        pygame.font.init()
        self.event_listener.start()
    
    def set_view(self, view):
       """
       Sets the currently active view.

       Args:
           view: The View instance to be displayed.
       """
       print(f"Switching view to {type(view).__name__}")
       self.current_view = view

def render(surface, display):
    """
    Renders the main drawing surface to the screen.
    On Raspberry Pi, it writes directly to the framebuffer.
    On other platforms, it updates the Pygame display window.
    """
    if IS_PI:
        try:
            with open("/dev/fb0", "wb") as framebuffer:
                framebuffer.write(surface.get_buffer())
        except IOError as e:
            print(f"Error writing to framebuffer: {e}")
            # Fallback or error handling could be added here
    else:
        if display:
            display.blit(surface, (0, 0))
        pygame.display.flip()

if __name__ == "__main__":
    try:
        app = Application()
        app.run()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)








