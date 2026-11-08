[app]
p4a.commit = 58d21141f17c889bf8585f5665921d72028f8831
p4a.local_recipes = ./recipes
android.minapi = 24
android.ndk_api = 24
title = Open Cifra
package.name = open_cifra
package.domain = com.kaykcaputo
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,md
source.exclude_dirs = tests,scripts,recipes,.venv,.git,__pycache__,build,dist
version = 0.3.1
requirements = python3, kivy==2.3.1, kivymd==1.2.0, pillow, numpy, charset_normalizer==3.5.2, requests, beautifulsoup4, typing_extensions, openssl, certifi, urllib3, chardet, idna, pyjnius
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,RECORD_AUDIO
android.api = 33
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.release_artifact = apk
android.allow_backup = True
android.presplash_color = #FFFFFF

[buildozer]
log_level = 2
warn_on_root = 1