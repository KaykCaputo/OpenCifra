# OpenCifra

OpenCifra is a Python application built with Kivy and KivyMD that serves as a songbook and lyrics viewer. It allows users to search for songs and artists, view lyrics with chords, and is designed to be mobile-friendly (Android).

## Features

- **Search**: Real-time search for songs and artists using an online API.
- **Lyrics & Chords**: View song lyrics with chords highlighted.
- **Chord Database**: Includes a comprehensive database of guitar chords.
- **Offline & Online**: Uses `guitar.json` for chord shapes (offline) and fetches song data online (CifraClub).
- **Responsive UI**: Material Design interface suited for mobile devices.

## Requirements

The project relies on the following Python packages:

- `python3`
- `kivy`
- `kivymd`
- `requests`
- `beautifulsoup4`
- `pyjnius`

And other dependencies automatically handled during the Android build process (openssl, certifi, etc.).

## Installation (Desktop)

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/OpenCifra.git
    cd OpenCifra
    ```

2.  **Set up a Virtual Environment**:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install kivy kivymd requests beautifulsoup4 pyjnius
    ```

## Usage

To run the application on your desktop:

```bash
python main.py
```

## Installation (Android)

You can download the latest pre-built APK suitable for your device from the [GitHub Releases](https://github.com/KaykCaputo/OpenCifra/releases) page.

1.  Download the `.apk` file.
2.  Install it on your device (you may need to enable "Install from Unknown Sources").

## Building for Android

If you prefer to build the APK yourself from source, this project is configured to use [Buildozer](https://github.com/kivy/buildozer).

1.  **Install Buildozer**:
    Follow the [official Buildozer installation guide](https://buildozer.readthedocs.io/en/latest/installation.html).

2.  **Build the APK**:

    ```bash
    buildozer android debug
    ```

    This command will download the Android SDK/NDK, compile the Python requirements, and generate the APK in the `bin/` directory.

3.  **Install on Android**:
    Transfer the generated `.apk` file from the `bin/` folder to your Android device and install it. You may need to enable "Install from Unknown Sources" in your device settings.

## File Structure

- `main.py`: The main application entry point containing the UI logic and API handling.
- `guitar.json`: A JSON database containing guitar chord variations and fingering positions.
- `buildozer.spec`: Configuration file for Buildozer, defining build requirements and permissions.

## Credits and Attributions

- **Chords Database**: The `guitar.json` chords database used in this project is from the [chords-db](https://github.com/tombatossals/chords-db) project by [tombatossals](https://github.com/tombatossals).
- **Lyrics Source**: The content of the chords is obtained through the CifraClub website.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
