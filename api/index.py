# -*- coding: utf-8 -*-
"""Entrypoint Serverless para Vercel (Python Runtime)."""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import MathAcademyHandler as handler  # noqa: E402, F401
