import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, "MI_PROYECTO")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from tactico_api import app
