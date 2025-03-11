# Games Detector

Fastattack, 2025

These python programs retrieve information about the game launchers on your computer like steam, epic games and GOG.

The programs can also create shortcuts for any games installed on the computer.

These programs are under MIT license which means you can use them and copy the code if necessary (even if a mention would be appreciated :D).

## Steam

The `steam_detector.py` file contains function to extract data about the steam launcher. It contains:
- A parser for the `appinfo.vdf` file
- A function to read the steam installation path (from the registry at `HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Valve\Steam\InstallPath`)
- A function to read steam libraries on the computer (at `STEAM_PATH\config\libraryfolders.vdf`)
- A function to read the installed games in the given library (from the manifest files (`appmanifest_APPID.acf`))
- A function to read what steam users are on this computer (at `STEAM_PATH\config\loginusers.vdf`)
- A function to create a shortcut for the given installed steam game (the icon from the games are stored at `STEAM_PATH\steam\games` and their names are stored in  `STEAM_PATH\appcache\appinfo.vdf`)

## Epic games

The `epic_detector.py` file contains function to extract data about the Epic Games launcher. It contains:
- A function to read the epic games launcher installation path
- A function to read the installation manifests (to get info about the installed games)
- A function to read the installed games on the computer
- A function to create a shortcut for the given installed epic game

## GOG

The `gog_detector.py` file contains function to extract data about the GOG galaxy launcher. It contains:
- A function to read the GOG galaxy installation path
- A function to read the installed games on the computer
- Functions to read information about the installed games from the registry
- A function to create a shortcut for the given installed GOG game

## Dependencies

The `epic_detector.py` and `gog_detector.py` only use modules directly included with python.

The `steam_detector.py` requires the installation of the `vdf` module (used to read steam files). You can install it from [here](https://github.com/ValvePython/vdf).
