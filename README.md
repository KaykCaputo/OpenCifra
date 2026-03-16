# OpenCifra

OpenCifra is a free and open-source Python application built with **Kivy** and **KivyMD** that serves as a songbook and lyrics viewer.

It allows users to search for songs and artists and view lyrics with chord notation in a mobile-friendly interface (desktop and Android).

⚠ **Official Repository**

The official source code of OpenCifra is hosted only at:

https://github.com/KaykCaputo/OpenCifra

Any other repository distributing binaries or modified versions should clearly reference this repository as the original source.

We have identified cases of third-party repositories using OpenCifra to distribute **malware**. Users must download binaries only from the official releases page of this repository.

This repository contains only the **source code** of the application.

---

# Screenshots

<p align="center">
  <img src="screenshot1.jpeg" width="300" alt="Search Screen"/>
  <img src="screenshot2.jpeg" width="300" alt="Lyrics Screen"/>
</p>

---

# Features

* Search songs and artists from public online sources
* Display lyrics with chord notation
* Responsive interface using **Kivy / KivyMD**
* Works on desktop and can be packaged for Android
* Fully free, open-source, and non-commercial

---

# Requirements

* Python 3.x
* Kivy
* KivyMD
* Requests
* BeautifulSoup4
* Pyjnius

Other dependencies (openssl, certifi, etc.) are automatically handled during the Android build process.

---

# Installation (Desktop)

Clone the repository:

```bash
git clone https://github.com/KaykCaputo/OpenCifra.git
cd OpenCifra

Create a virtual environment:

python3 -m venv .venv

Activate it:

Linux/macOS

source .venv/bin/activate

Windows

.venv\Scripts\activate

Install dependencies:

pip install kivy kivymd requests beautifulsoup4 pyjnius

Run the application:

python main.py


---

Installation (Android)

Download the latest official APK from the GitHub Releases page of this repository only.

Installing APKs from other repositories is not recommended and may pose security risks.

You may need to enable Install from Unknown Sources on your device.


---

Building from Source (Android)

This project uses Buildozer.

1. Install Buildozer following the official guide


2. Build the APK:



buildozer android debug

3. Transfer the .apk file from the bin/ folder to your device and install it.




---

File Structure

main.py — Main application entry point containing UI logic and API handling

guitar.json — Database of guitar chords and finger positions

buildozer.spec — Build configuration for Android packaging



---

Legal Notice

OpenCifra does not store, host, or redistribute copyrighted lyrics or musical works.

All lyrics and chords displayed are:

Retrieved in real time from public web sources

Displayed temporarily at the user’s request

Owned by their respective authors and copyright holders


OpenCifra functions as a client-side viewer, similar to a web browser, and does not maintain its own database of musical works.

If you are a copyright holder and believe that content accessed through this application infringes your rights, please open an issue in this repository.


---

Privacy

OpenCifra does not:

Collect personal data

Track users

Use analytics

Store song content on servers


All processing happens locally on the user's device.


---

Educational Purpose

OpenCifra is intended for:

Music students

Practice and study

Educational and non-commercial use


The project aims to democratize access to music learning tools through free and open-source software.


---

Contributions

Contributions are welcome.

You can:

Open issues

Submit pull requests

Improve documentation

Suggest architectural or legal improvements


Please ensure contributions respect open-source principles and copyright.


---

Forking and Redistribution

Forks are strongly recommended over copying manually.

To maintain transparency and reduce confusion:

Fork this repository instead of copying it manually

Clearly reference the original project

Provide attribution to the original repository


Recommended attribution example:

This project is based on OpenCifra
https://github.com/KaykCaputo/OpenCifra

Repositories redistributing this project should not present themselves as the original source.


---

Security Notice

Only download binaries and APK files from the official releases page of this repository.

Third-party repositories may distribute modified versions of this software or binaries containing malware.

The maintainer of OpenCifra does not verify or endorse builds distributed outside the official repository.


---

License

This project is licensed under the MIT License.

You are free to:

Use

Modify

Distribute

Fork


As long as the original copyright notice and license text remain included.


---

Optional Donations

Donations are voluntary and intended only to support the development of the open-source software.

They do not provide access to musical content or additional features.


---

Disclaimer

This software is provided "as is", without warranty of any kind.

The authors are not responsible for the use of third-party content accessed by users through this application.