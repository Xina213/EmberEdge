#!/usr/bin/env python3
"""Teste imports básicos EmberEdge"""

print("🔍 Testando imports...")

try:
    import flask
    print("✅ Flask OK")
except ImportError:
    print("❌ Flask FALTA")

try:
    from flask_cors import CORS
    print("✅ Flask-CORS OK")
except ImportError:
    print("❌ Flask-CORS FALTA")

try:
    import sklearn
    print("✅ Scikit-learn OK")
except ImportError:
    print("❌ Scikit-learn FALTA")

try:
    import pandas as pd
    print("✅ Pandas OK")
except ImportError:
    print("❌ Pandas FALTA")

try:
    import numpy as np
    print("✅ Numpy OK")
except ImportError:
    print("❌ Numpy FALTA")

try:
    import joblib
    print("✅ Joblib OK")
except ImportError:
    print("❌ Joblib FALTA")

try:
    from dotenv import load_dotenv
    print("✅ Python-dotenv OK")
except ImportError:
    print("❌ Python-dotenv FALTA")

print("\n🎉 Setup completo! Pronto para FASE 2.")
