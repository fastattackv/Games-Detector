"""
This file contains functions to read information about GOG galaxy and installed GOG games on the current computer.
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


import os
import shutil
import winreg
from win32com.client import Dispatch


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


def read_gog_launcher_path() -> str:
    r"""Reads the gog galaxy launcher path from the registry and returns the path where the launcher is installed at

    :return: path of the launcher (usually: "C:\Program Files (x86)\GOG Galaxy")
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\GalaxyClient\paths")
    except FileNotFoundError:
        print("incorrect base key")
    except Exception as e:
        print("error: ", e)
    else:
        try:
            val = winreg.QueryValueEx(key, "client")
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


def read_installed_games() -> dict[str, str]:
    """Returns the installed GOG games from the registry

    :return: installed games: {gameID1: "game1", gameID2: "game2"}
    """
    games = {}
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\Games")
    except FileNotFoundError:
        print("incorrect base key")
    except Exception as e:
        print("error: ", e)
    else:
        index = 0
        while True:
            try:
                gameID = winreg.EnumKey(key, index)
                index += 1
            except OSError:
                break
            else:
                try:
                    game_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fr"SOFTWARE\WOW6432Node\GOG.com\Games\{gameID}")
                    game_name = winreg.QueryValueEx(game_key, "gameName")[0]
                except FileNotFoundError:
                    print("incorrect base key")
                except Exception as e:
                    print("error: ", e)
                else:
                    games[gameID] = game_name
    return games


def read_game_installation(gameID: str) -> str:
    """Returns the installation of the given gog game from the registry

    :param gameID: gameID to return the installation path
    :return: installation path of the given game
    """
    try:
        game_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fr"SOFTWARE\WOW6432Node\GOG.com\Games\{gameID}")
        game_installation = winreg.QueryValueEx(game_key, "path")[0]
    except FileNotFoundError:
        print("incorrect base key")
    except Exception as e:
        print("error: ", e)
    else:
        return game_installation


def read_game_working_directory(gameID: str) -> str:
    """Returns the working directory of the given gog game from the registry

    :param gameID: gameID to return the wd
    :return: working directory of the given game
    """
    try:
        game_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fr"SOFTWARE\WOW6432Node\GOG.com\Games\{gameID}")
        game_installation = winreg.QueryValueEx(game_key, "workingDir")[0]
    except FileNotFoundError:
        print("incorrect base key")
    except Exception as e:
        print("error: ", e)
    else:
        return game_installation


def read_game_valid_name(gameID: str) -> str:
    """Returns the name of the given game so it is a valid windows filename from the registry

    :param gameID: game id to retrieve the name from
    :return: name of the game
    """
    try:
        game_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fr"SOFTWARE\WOW6432Node\GOG.com\Games\{gameID}")
        game_name = winreg.QueryValueEx(game_key, "startMenu")[0]
    except FileNotFoundError:
        print("incorrect base key")
    except Exception as e:
        print("error: ", e)
    else:
        return game_name


def create_game_shortcut(gameID: str, output_dir: str) -> str:
    """Creates a shortcut to the given directory for the given game

    :param gameID: game id of the game to create a shortcut for
    :param output_dir: directory to create the shortcut to
    :return: path of the created shortcut
    """
    if os.path.isdir(output_dir):
        installation = read_game_installation(gameID)
        name = read_game_valid_name(gameID)
        wd = read_game_working_directory(gameID)
        target_path = os.path.normpath(os.path.join(read_gog_launcher_path(), "GalaxyClient.exe"))
        arguments = f'/command=runGame /gameId={gameID} /path="{installation}"'
        final_path = os.path.join(output_dir, get_valid_file_name(name + ".lnk"))
        try:
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(final_path)
            shortcut.Targetpath = target_path
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = wd
            shortcut.IconLocation = os.path.join(installation, f"goggame-{gameID}.ico")
            shortcut.save()
        except Exception as e:
            print("failed for", gameID, e)
            final_path = shutil.copy2(os.path.join(installation, f"Launch {name}.lnk"), os.path.join(output_dir, get_valid_file_name(name + ".lnk")))
        return final_path
    else:
        print("the given output dir does not exist")


print("GOG path:", read_gog_launcher_path())
games = read_installed_games()
print("Installed games:", list(games.values()))
if input("Do you want to create shortcuts for these games ? [y/n]: ") == "y":
    for game_id in games:
        print("Created shortcut at:", create_game_shortcut(game_id, "C:/Users/fastattack/Desktop/test"))
print("Done!")
