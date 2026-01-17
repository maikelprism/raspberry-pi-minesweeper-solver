import pygame
import config

class AssetManager:
    """
    A centralized manager for loading, storing, and retrieving game assets.
    This ensures that fonts and images are loaded only once.
    """
    def __init__(self):
        """Initializes the AssetManager and pre-loads all assets."""
        self.fonts = {}
        self.images = {}
        self.load_assets()

    def load_assets(self):
        """Loads all game fonts and images specified in the config."""
        # Fonts
        self.load_font("regular", config.FontPaths.JERSEY_15, config.FontSizes.REGULAR)
        self.load_font("subtext", config.FontPaths.JERSEY_15, config.FontSizes.SUBTEXT)
        self.load_font("title", config.FontPaths.JERSEY_15, config.FontSizes.TITLE)

        # Images
        self.load_image("crosshair", config.ImagePaths.CROSSHAIR)
        self.load_image("asteroid", config.ImagePaths.ASTEROID)
        self.load_image("background", config.ImagePaths.BACKGROUND)

    def load_font(self, name, path, size):
        """
        Loads a font from a file and stores it in the manager.

        Args:
            name: The key to store the font under.
            path: The file path to the font.
            size: The size to load the font in.
        """
        self.fonts[name] = pygame.font.Font(path, size)

    def load_image(self, name, path):
        """
        Loads an image from a file and stores it in the manager.

        Args:
            name: The key to store the image under.
            path: The file path to the image.
        """
        self.images[name] = pygame.image.load(path)

    def get_font(self, name):
        """
        Retrieves a pre-loaded font.

        Args:
            name: The key of the font to retrieve.

        Returns:
            A pygame.font.Font object.
        """
        return self.fonts.get(name)

    def get_image(self, name):
        """
        Retrieves a pre-loaded image.

        Args:
            name: The key of the image to retrieve.

        Returns:
            A pygame.Surface object.
        """
        return self.images.get(name)
