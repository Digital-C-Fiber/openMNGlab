from dataclasses import dataclass
from typing import Sequence, Optional
import seaborn as sns


@dataclass
class Theme:
    """see seaborn.set_theme"""
    context: str | dict = 'notebook'
    style: str | dict = 'darkgrid'
    palette: str | Sequence = 'deep'
    font: str = 'sans-serif'
    font_scale: int = 1
    color_codes: bool = True
    rc: Optional[dict] = None

    def __enter__(self):
        sns.set_theme(self.context, self.style, self.palette, self.font, self.font_scale, self.color_codes, self.rc)

    def __exit__(self, exc_type, exc_val, exc_tb):
        sns.reset_orig()


