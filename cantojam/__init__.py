"""cantojam (協音): melody and tone fit for Cantonese lyrics."""

from .check import check, parse_degrees, parse_melody
from .contour import build_contour, render
from .fit import repairs
from .jyutping import Lexicon, syllabify, tone_of
from .lexicon import Lexicon as WordList, rime
from .midi import read as read_midi
from .model import ToneModel

__version__ = "0.2.0"
__all__ = ["check", "parse_degrees", "parse_melody", "build_contour", "render",
           "repairs", "Lexicon", "syllabify", "tone_of", "read_midi",
           "ToneModel", "WordList", "rime"]
