"""
KURSORIN Theme System

Defines the Arctic Terminal design system:
- Deep navy backgrounds with electric cyan accents
- Typography constants
- Component style presets for CustomTkinter
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class KursorinPalette:
    """Color palette — Arctic Terminal aesthetic."""

    # Backgrounds (layered depth)
    bg_deepest: str = "#060b14"       # Window background
    bg_deep: str = "#0a0f1a"          # Main panels
    bg_surface: str = "#111827"       # Card surfaces
    bg_elevated: str = "#1a2332"      # Elevated panels / hover states
    bg_input: str = "#0f172a"         # Input backgrounds

    # Foregrounds
    fg_primary: str = "#e2e8f0"       # Primary text
    fg_secondary: str = "#94a3b8"     # Secondary text
    fg_muted: str = "#475569"         # Muted / disabled
    fg_inverse: str = "#0a0f1a"       # Text on bright backgrounds

    # Accents
    accent_cyan: str = "#06d6a0"      # Primary accent (electric cyan-green)
    accent_cyan_hover: str = "#05c493" 
    accent_cyan_dim: str = "#064e3b"  # Dimmed cyan for subtle highlights
    accent_blue: str = "#38bdf8"      # Secondary accent (sky blue)
    accent_amber: str = "#f59e0b"     # Warning / caution
    accent_red: str = "#ef4444"       # Error / destructive
    accent_purple: str = "#a78bfa"    # Info / highlight

    # Borders
    border_subtle: str = "#1e293b"    # Subtle borders
    border_default: str = "#334155"   # Default borders
    border_focus: str = "#06d6a0"     # Focus ring

    # Status
    status_online: str = "#06d6a0"
    status_offline: str = "#ef4444"
    status_warning: str = "#f59e0b"
    status_idle: str = "#475569"

    # Overlay
    overlay_bg: str = "#000000"
    overlay_opacity: float = 0.7


# Singleton palette
PALETTE = KursorinPalette()


@dataclass(frozen=True)
class KursorinTypography:
    """Typography constants."""

    # Font families (CustomTkinter uses system fonts)
    family_display: str = "Segoe UI"      # Windows primary
    family_body: str = "Segoe UI"
    family_mono: str = "Cascadia Code"      # Monospace

    # Sizes
    size_hero: int = 28
    size_h1: int = 22
    size_h2: int = 18
    size_h3: int = 15
    size_body: int = 13
    size_small: int = 11
    size_tiny: int = 10

    # Weights
    weight_bold: str = "bold"
    weight_normal: str = "normal"


TYPO = KursorinTypography()


@dataclass(frozen=True)
class KursorinSpacing:
    """Spacing scale (px)."""

    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32
    xxxl: int = 48

    # Radius
    radius_sm: int = 4
    radius_md: int = 8
    radius_lg: int = 12
    radius_xl: int = 16


SPACING = KursorinSpacing()


def apply_theme():
    """Apply the custom theme to CustomTkinter."""
    try:
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
    except ImportError:
        pass


def get_ctk_colors() -> Dict:
    """Get CTK-compatible color tuples (dark_mode, light_mode).
    Since we only support dark mode, both are the same."""
    p = PALETTE
    return {
        "fg_color": (p.bg_surface, p.bg_surface),
        "hover_color": (p.bg_elevated, p.bg_elevated),
        "border_color": (p.border_subtle, p.border_subtle),
        "text_color": (p.fg_primary, p.fg_primary),
        "text_color_secondary": (p.fg_secondary, p.fg_secondary),
        "button_color": (p.accent_cyan, p.accent_cyan),
        "button_hover_color": (p.accent_cyan_hover, p.accent_cyan_hover),
        "button_text_color": (p.fg_inverse, p.fg_inverse),
    }
