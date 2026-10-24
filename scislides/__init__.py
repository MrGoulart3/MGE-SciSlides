"""MGE-SciSlides: build, check and render scientific presentations with python-pptx."""
from .deck import Deck
from .theme import PRESETS, Theme, contrast_ratio, get_theme, load_theme

__version__ = "0.1.0"
__all__ = ["Deck", "Theme", "PRESETS", "get_theme", "load_theme", "contrast_ratio"]
