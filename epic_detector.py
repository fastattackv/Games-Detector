"""
This file contains functions to read information about the epic games launcher and installed games on the current computer.
It also allows to create shortcuts for the installed games.

MIT License

Copyright (c) 2025 Fastattack

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE
"""


import winreg
import os
import json


def get_valid_file_name(filename: str) -> str:
    """Modifies a given filename to remove any forbidden characters from it

    :param filename: filename to check
    :return: valid filename (if the filename was already valid, returns the unchanged filename)
    """
    forbidden_chars = ["/", "\\", ":", "*", "?", "\"", "<", ">", "|"]
    # remove forbidden characters
    for char in forbidden_chars:
        if char in filename:
            filename = filename.replace(char, " ")

    # remove spaces at the end or beginning of the filename
    while filename.startswith(" "):
        filename = filename.removeprefix(" ")
    while filename.endswith(" "):
        filename = filename.removesuffix(" ")
    return filename


def read_epic_launcher_path() -> str:
    r"""Reads the epic games launcher path from the registry and returns the path where the launcher is installed at

    :return: path of the directory to the manifests (usually: "C:\Program Files (x86)\Epic Games")
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Epic Games\EOS\InstallHelper")
    except FileNotFoundError:
        print("incorrect base key")
    except Exception as e:
        print("error: ", e)
    else:
        try:
            val = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            print("incorrect key")
        except Exception as e:
            print(e)
        else:
            path = val[0]
            if path.endswith(r"\Epic Online Services\EpicOnlineServicesInstallHelper.exe"):
                path = path.removesuffix(r"\Epic Online Services\EpicOnlineServicesInstallHelper.exe")
            if os.path.isdir(path):
                return path
            else:
                print("path does not exist")


def read_epic_manifests_path() -> str:
    r"""Reads the epic games launcher path from the registry and returns the path where the manifests are stored

    :return: path of the directory to the manifests (usually: "C:/ProgramData/Epic/EpicGamesLauncher/Data/Manifests")
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Epic Games\EOS")
    except FileNotFoundError:
        print("incorrect base key")
    except Exception as e:
        print("error: ", e)
    else:
        try:
            val = winreg.QueryValueEx(key, "ModSdkMetadataDir")
        except FileNotFoundError:
            print("incorrect key")
        except Exception as e:
            print(e)
        else:
            path = val[0]
            if os.path.isdir(path):
                return path
            else:
                print("path does not exist")


def read_epic_games_installed(manifests_folder: str) -> dict[str, str]:
    """Reads what epic games are installed on the computer using the manifests directory

    :param manifests_folder: folder containing the manifests of installation
    :return: dictionary containing the installed games: {"game1": "manifest_path", "game2": "manifest_path"}
    """
    installed_games = {}
    for item in os.listdir(manifests_folder):
        file_path = os.path.normpath(os.path.join(manifests_folder, item))
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                installed_games[content["DisplayName"]] = file_path
    return installed_games


def create_game_shortcut(manifest_file: str, output_dir: str) -> str:
    """Creates a shortcut to the given directory for the given game

    :param manifest_file: manifest file of installation of the gale to create the shortcut from
    :param output_dir: directory to create the shortcut to
    :return: path of the created shortcut
    """
    if os.path.isfile(manifest_file):
        if os.path.isdir(output_dir):

            # get the needed info
            working_dir = read_epic_launcher_path()
            with open(manifest_file, "r", encoding="utf-8") as f:
                content = json.load(f)
                url = f"com.epicgames.launcher://apps/{content["CatalogNamespace"]}%3A{content["CatalogItemId"]}%3A{content["AppName"]}?action=launch&silent=true"
                icon_path = os.path.normpath(os.path.join(content["InstallLocation"], content["LaunchExecutable"]))
                final_path = os.path.normpath(os.path.join(output_dir, get_valid_file_name(content["DisplayName"]) + ".url"))

            # write the info to the shortcut
            text = ("[{000214A0-0000-0000-C000-000000000046}]\n"
                    "Prop3=19,0\n"
                    "[InternetShortcut]\n"
                    "IDList=\n"
                    "IconIndex=0\n"
                    f"WorkingDirectory={working_dir}\n"
                    f"URL={url}\n"
                    f"IconFile={icon_path}\n")
            with open(final_path, "w", encoding="utf-8") as f:
                f.write(text)

            return final_path
        else:
            print("the given output dir does not exist")
    else:
        print("the given manifest file does not exist")


epic_path = read_epic_launcher_path()
print("Epic games launcher path:", epic_path)
manifests_path = read_epic_manifests_path()
print("Path to manifests files:", manifests_path)
games = read_epic_games_installed(manifests_path)
print("Installed games", ", ".join(games.keys()))
if input("Do you want to create shortcuts for these games ? [y/n]: ") == "y":
    for game in games:
        print("Created shortcut at:", create_game_shortcut(games[game], "C:/Users/fastattack/Desktop/test"))
print("Done!")
