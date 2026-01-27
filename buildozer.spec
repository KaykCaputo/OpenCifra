[app]
title = Open Cifra
package.name = open_cifra
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf
version = 0.1
requirements = python3, kivy, kivymd, requests, beautifulsoup4, typing_extensions, openssl, certifi, urllib3, chardet, idna, pyjnius
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.presplash_color = #FFFFFF

[buildozer]
log_level = 2
warn_on_root = 1