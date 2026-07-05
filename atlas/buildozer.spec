[app]

title = Atlas
package.name = atlas
package.domain = org.atlas

source.dir = .
version = 1.0.0

# -------------------------
# SOURCE FILES
# -------------------------
source.include_exts = py,png,jpg,jpeg,kv,db,json,txt

source.include_patterns =
    assets/*,
    data/*,
    core/*,
    database/*,
    utils/*,
    android/*

source.exclude_dirs = windows,__pycache__,.git,.github,bin,venv,tests
source.exclude_patterns = *.pyc,*.pyo,*.log

# -------------------------
# PYTHON DEPENDENCIES
# -------------------------
# ⚠️ Android-compatible versions only
requirements = python3,kivy,plyer,numpy,scikit-learn,nltk,sqlite3

# -------------------------
# ANDROID CONFIG
# -------------------------
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

android.archs = arm64-v8a

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.accept_sdk_license = True

# -------------------------
# KIVY BACKEND
# -------------------------
p4a.bootstrap = sdl2

# -------------------------
# UI / APP
# -------------------------
orientation = portrait
fullscreen = 0

icon.filename = assets/icons/icon.png
presplash.filename = assets/icons/splash.png

android.background_color = #0a1628

# -------------------------
# LOGS
# -------------------------
log_level = 2
warn_on_root = 1