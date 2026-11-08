# OpenCifra v0.3 — Release Notes

OpenCifra v0.3 expands the original chord-sheet viewer into a guitar practice companion, adding personal song lists, chord tools, reading controls, alternate tunings and a built-in tuner.

## New features

- **Favorites and recent songs:** Create named lists, save or remove songs, and revisit recently opened songs. Lists and preferences are stored locally.
- **Interactive chord diagrams:** View fingerings above the song and tap chords to explore alternate positions. A chord generator supports extensions, alterations, slash chords and Brazilian `7M` notation, with clear feedback when a valid shape cannot be generated.
- **Six guitar tunings:** Standard, Drop D, half-step down, DADGAD, Open G and Open D. The selected tuning updates chord fingerings and tuner targets.
- **Transposition and capo controls:** Change the song key by semitone, adjust capo position while preserving sounding pitch, and reset to the original key.
- **More comfortable reading:** Adjust font size, show or hide tablature, and enable automatic scrolling with adjustable speed. Touching the sheet pauses scrolling.
- **Integrated OpenTuna tuner:** Chromatic tuning, individual string targets, a cents meter and FFT-based pitch detection. Microphone access starts on request and stops when leaving the tuner or suspending the app.

## Improvements and fixes

- More responsive search with debouncing, protection against outdated responses, and bounded in-memory caches.
- Better chord-sheet parsing, chord spacing after transposition, safe markup rendering and preservation of source credits.
- Clearer feedback and retry handling for unavailable songs and network errors.
- Expanded automated tests, development checks and reproducible Android build/release tooling.

## Android download and compatibility

- Signed Android APK for `arm64-v8a` and `armeabi-v7a`, supporting Android 7.0 (API 24) and later.
- **Package identifier changed** from `org.test.open_cifra` to `com.kaykcaputo.open_cifra`. The new APK cannot update an installation of the old package in place; locally stored app data is not migrated automatically.
- Internet access is required to search for and retrieve songs. Favorites store song references, not offline copies of lyrics.
- Transposition changes chord symbols, not tablature fret numbers. Selecting a tuning changes the suggested fingerings and tuner targets; it does not retune the instrument.

Thanks to [@Prosperteni](https://github.com/Prosperteni) for the exception-handling contribution in [#9](https://github.com/KaykCaputo/OpenCifra/pull/9).

**Full changes:** [pre-release-v0.2...v0.3](https://github.com/KaykCaputo/OpenCifra/compare/pre-release-v0.2...v0.3)
