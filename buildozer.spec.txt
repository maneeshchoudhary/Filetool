[app]
title = File Tool
package.name = filetool
package.domain = org.maneesh

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

# Libraries needed on Android
requirements = python3,kivy,pandas,openpyxl,xlrd,pillow,reportlab,pypdf,pdfplumber

# Android settings
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

# Orientation
orientation = portrait

# Icon (optional — rakh sakte ho apni icon)
# icon.filename = icon.png

# Fullscreen nahi
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
