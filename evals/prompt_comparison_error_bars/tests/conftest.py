"""Make the recipe's modules importable the way the notebook imports them."""

import sys
from pathlib import Path

RECIPE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RECIPE_DIR))
