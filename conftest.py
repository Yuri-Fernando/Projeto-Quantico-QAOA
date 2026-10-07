"""Garante que a raiz do projeto esteja no sys.path ao rodar pytest daqui."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
