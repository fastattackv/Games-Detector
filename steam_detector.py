"""
This file contains functions to read information about steam and installed steam games on the current computer.
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
import vdf
import struct


def read_appinfo(path: str) -> dict:
    """Reads the given appinfo file and returns a dict containing info stocked in the file. Greatly helped by https://github.com/SteamDatabase/SteamAppInfo

    :param path: path of the file to read
    :return: dict containing {appid: {infos}}
    """
    int32 = struct.Struct('<I')  # 4 bytes
    int64 = struct.Struct('<Q')  # 8 bytes

    return_dict = {}
    with open(path, "rb") as f:

        # read basic info (almost useless in this case)
        magic = f.read(4)
        if magic != b")DV\x07":
            raise SyntaxError("Invalid magic, got %s" % repr(magic))
        universe = int32.unpack(f.read(4))[0]
        string_table_offset = int64.unpack(f.read(8))[0]
        previous_offset = f.tell()
        f.seek(previous_offset + string_table_offset)
        string_count = int32.unpack(f.read(4))[0]
        f.seek(previous_offset)

        # read game infos
        while True:
            appid = int32.unpack(f.read(4))[0]
            if appid == 0:
                break

            size = int32.unpack(f.read(4))[0]
            end = f.tell() + size

            app = {
                'appid': appid,
                'info_state': int32.unpack(f.read(4))[0],
                'last_updated': int32.unpack(f.read(4))[0],
                'picsToken': int64.unpack(f.read(8))[0],
                'sha1Text': f.read(20),
                'change_number': int32.unpack(f.read(4))[0],
                'sha1Binary': f.read(20),
                'name': None,
                'type': None,
                'icon_hash': None,
                'binary_content': f.read(end - f.tell())
            }

            # read the name of the game (is separated by \x01\x04\x00\x00\x00)
            name = b""
            if b"\x01\x04\x00\x00\x00" in app["binary_content"]:
                index = app["binary_content"].index(b"\x01\x04\x00\x00\x00") + 5
                while app["binary_content"][index:index + 1] != b"\x00":
                    name += app["binary_content"][index:index + 1]
                    index += 1
                app["name"] = bytes.decode(name)

            # read the type of item (is separated by \x01\x05\x00\x00\x00)
            obj_type = b""
            if b"\x01\x05\x00\x00\x00" in app["binary_content"]:
                index = app["binary_content"].index(b"\x01\x05\x00\x00\x00") + 5
                while app["binary_content"][index:index + 1] != b"\x00":
                    obj_type += app["binary_content"][index:index + 1]
                    index += 1
                if obj_type in [b"Game", b"DLC", b"Demo", b"Config", b"Beta", b"Tool", b"ownersonly", b"Application"]:
                    app["type"] = bytes.decode(obj_type)

            # read the icon hash (is separated by \x01X\x01\x00\x00 and is 40 bytes long)
            if b"\x01X\x01\x00\x00" in app["binary_content"]:
                index = app["binary_content"].index(b"\x01X\x01\x00\x00") + 5
                app["icon_hash"] = bytes.decode(app["binary_content"][index: index + 40])

            return_dict[appid] = app

    return return_dict


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


def read_steam_path() -> str | None:
    r"""Reads the steam installation path from the registry and returns the path where steam is installed at

    :return: path of the directory to the manifests (usually: "C:\Program Files (x86)\Steam")
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
    except FileNotFoundError:
        print("incorrect base key")
    except Exception as e:
        print("error: ", e)
    else:
        try:
            val = winreg.QueryValueEx(key, "InstallPath")
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


def read_steam_libraries(steam_path=None) -> list[str] | None:
    r"""Returns the path where the manifests are stored for the steam library

    :param steam_path: steam installation path (optional, if set to None, it will automatically read the steam installation in the registry)
    :return: path of the directory to the manifests (usually: "C:\Program Files (x86)\Steam\steamapps")
    """
    libs = []
    if steam_path is None:
        steam_path = read_steam_path()
    if os.path.isdir(os.path.join(steam_path, "steamapps")) and os.path.isfile(os.path.join(steam_path, "steamapps", "libraryfolders.vdf")):
        path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    elif os.path.isdir(os.path.join(steam_path, "config")) and os.path.isfile(os.path.join(steam_path, "config", "libraryfolders.vdf")):
        path = os.path.join(steam_path, "config", "libraryfolders.vdf")
    else:
        print("incorrect path or file containing libraries path does not exist")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = vdf.load(f)
    for lib in content["libraryfolders"]:
        path = os.path.normpath(os.path.join(content["libraryfolders"][lib]["path"], "steamapps"))
        if os.path.isdir(path):
            libs.append(path)
        else:
            print(f"path to library n°{lib} does not exist")
    return libs


def read_steam_games_installed(library_folder: str) -> dict[str, int]:
    """Reads what steam games are installed in the given library

    :param library_folder: folder containing the manifests of installation
    :return: dictionary containing the installed games: {"game1": appid, "game2": appid}
    """
    installed_games = {}
    for item in os.listdir(library_folder):
        file_path = os.path.normpath(os.path.join(library_folder, item))
        if os.path.isfile(file_path) and file_path.endswith(".acf"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = vdf.load(f)
                if content["AppState"]["appid"] != "228980":  # excludes Steamworks Common Redistributables
                    installed_games[content["AppState"]["name"]] = int(content["AppState"]["appid"])
    return installed_games


def read_users_ids() -> dict[str, str] | None:
    """Reads the different users on the local machine and their ids

    :return: dict containing the username and ids: {"username1": "id1", "username2": "id2"}
    """
    user_ids = {}
    steam_path = read_steam_path()
    path = os.path.join(steam_path, "config", "loginusers.vdf")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            content = vdf.load(f)
            for user_id in content["users"]:
                user_ids[content["users"][user_id]["AccountName"]] = user_id
        return user_ids
    else:
        print("incorrect path")


def create_games_shortcut(appid: int, appinfo_dict: dict, output_dir: str) -> str | None:
    """Creates a shortcut to the given directory for the given game

    :param appid: appid of the game to create a shortcut for
    :param appinfo_dict: appinfo dict extracted by appinfo_parser.py from the appinfo.vdf file
    :param output_dir: directory to create the shortcuts to
    :return: paths of the created shortcuts
    """
    if appid not in appinfo_dict:
        print("The given appid is not present in the given appinfo_dict")
        return

    if os.path.isdir(output_dir):
        # get the needed info
        url = f"steam://rungameid/{appid}"
        path = os.path.normpath(os.path.join(read_steam_path(), "steam/games", appinfo_dict[appid]["icon_hash"] + ".ico"))
        if os.path.isfile(path):
            icon_path = path
        else:
            icon_path = ""
        final_path = os.path.normpath(os.path.join(output_dir, get_valid_file_name(appinfo_dict[appid]["name"]) + ".url"))

        # write the info to the shortcut
        text = ("[{000214A0-0000-0000-C000-000000000046}]\n"
                "Prop3=19,0\n"
                "[InternetShortcut]\n"
                "IDList=\n"
                "IconIndex=0\n"
                f"URL={url}\n"
                f"IconFile={icon_path}\n")
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(text)

        return final_path
    else:
        print("the given output dir does not exist")


steam_path = read_steam_path()
print("Steam path:", steam_path)
libs = read_steam_libraries()
print("Found libraries:", libs)
users = read_users_ids()
print("Found users:", users)
games = {}
for lib in libs:
    games = games | read_steam_games_installed(lib)
print("Installed games found:", list(games.keys()))
if input("Do you want to create shortcuts for these games ? [y/n]: ") == "y":
    appinfo = read_appinfo(os.path.join(read_steam_path(), "appcache/appinfo.vdf"))
    for appid in games.values():
        print("Created shortcut at:", create_games_shortcut(appid, appinfo, "C:/Users/fastattack/Desktop/test"))
print("Done!")
