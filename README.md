# OpenCifra

OpenCifra is a free and open-source Python application built with **Kivy** and **KivyMD** that serves as a songbook and lyrics viewer.

It allows users to search for songs and artists and view lyrics with chord notation in a mobile-friendly interface (desktop and Android).

---

## Official Repository

The official source code of OpenCifra is hosted only at:

[https://github.com/KaykCaputo/OpenCifra](https://github.com/KaykCaputo/OpenCifra)

> **Security Warning:** Any other repository distributing binaries or modified versions should clearly reference this repository as the original source. We have identified cases of third-party repositories using OpenCifra to distribute malware. Users must download binaries only from the official releases page of this repository.

---

## Screenshots

<p align="center">
  <img src="screenshot1.jpeg" width="300" alt="Search Screen"/>
  <img src="screenshot2.jpeg" width="300" alt="Lyrics Screen"/>
</p>

---

## Features

* Search songs and artists from public online sources
* Display lyrics with chord notation
* Responsive interface using **Kivy / KivyMD**
* Works on desktop and can be packaged for Android
* Fully free, open-source, and non-commercial

---

## Requirements

* Python 3.x
* Kivy
* KivyMD
* Requests
* BeautifulSoup4
* Pyjnius

---

## Installation (Desktop)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/KaykCaputo/OpenCifra.git
   cd OpenCifra
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   ```

3. **Activate it:**
   - **Linux/macOS:** `source .venv/bin/activate`
   - **Windows:** `.venv\Scripts\activate`

4. **Install dependencies:**
   ```bash
   pip install kivy kivymd requests beautifulsoup4 pyjnius
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

---

## Installation (Android)

Download the latest official APK from the **GitHub Releases** page of this repository only. Installing APKs from other repositories is not recommended and may pose security risks.

### Building from Source (Android)

This project uses **Buildozer**.

1. Install Buildozer following the official guide.
2. Build the APK:
   ```bash
   buildozer android debug
   ```
3. Transfer the `.apk` file from the `bin/` folder to your device.

---

## File Structure

* `main.py` — Main application entry point containing UI logic and API handling.
* `guitar.json` — Database of guitar chords and finger positions.
* `buildozer.spec` — Build configuration for Android packaging.

---

## Legal Notice

OpenCifra does not store, host, or redistribute copyrighted lyrics or musical works. All lyrics and chords displayed are:

* Retrieved in real time from public web sources.
* Displayed temporarily at the user’s request.
* Owned by their respective authors and copyright holders.

OpenCifra functions as a client-side viewer, similar to a web browser. If you are a copyright holder and believe that content accessed through this application infringes your rights, please open an issue in this repository.

---

## Privacy

OpenCifra does not collect personal data, track users, use analytics, or store song content on servers. All processing happens locally on the user's device.

---

## Educational Purpose

OpenCifra is intended for music students, practice, and study for educational and non-commercial use. The project aims to democratize access to music learning tools through free and open-source software.

---

## Contributions and Forking

Contributions are welcome via issues and pull requests.

**Forking Guidelines:**

* Fork this repository instead of copying it manually to maintain transparency.
* Clearly reference the original project.
* Provide attribution: *This project is based on OpenCifra (https://github.com/KaykCaputo/OpenCifra)*.

---

## License

This project is licensed under the **MIT License**. You are free to use, modify, and distribute the software as long as the original copyright notice and license text remain included.

---

## Disclaimer

This software is provided "as is", without warranty of any kind. The authors are not responsible for the use of third-party content accessed by users through this application.
