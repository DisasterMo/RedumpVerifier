from difflib import SequenceMatcher
import ast
import datetime
import hashlib
import os
import sys

dats = os.listdir("./dat")
read_size = 1024

romList = list()
romListRedumpName = list()
romListHash = list()


def get_all_files(dir_name):
    files = os.listdir(dir_name)
    all_files = list()

    for entry in files:
        full_path = os.path.join(dir_name, entry)
        if os.path.isdir(full_path):
            all_files = all_files + get_all_files(full_path)
        else:
            all_files.append(full_path)

    return all_files


def verify(files):
    global dats, romList, romListRedumpName, romListHash
    for file in files:
        print("\nISO: " + file)
        hasher = hashlib.md5()
        print("Calculating hash...")
        with open(file, "rb") as f:
            data = f.read(read_size)
            while data:
                hasher.update(data)
                data = f.read(read_size)
        md5hash = hasher.hexdigest()

        romList.append(file)

        game_name = get_fast_match(dats, md5hash)

        if game_name:
            romListRedumpName.append(game_name)
        else:
            print("ISO's MD5: " + md5hash
                  + "\n"
                  + "ISO's MD5 doesn't match any Redump hash"
                  + "\n"
                  + "\n"
                  + "----------------------------------------"
                  )
            romListRedumpName.append("Not verified")

        romListHash.append(md5hash)


def print_match(md5hash, game_name, dat):
    print("\n"
          + "ISO's MD5 hash: " + md5hash
          + "\n"
          + "Game Verified, ISO's MD5 matches Redump hash"
          + "\n"
          + f"Redump game name: {game_name} ({dat})"
          + "\n"
          + "----------------------------------------")


def get_game_name(data, name_line):
    while "<description>" not in data[name_line]:
        name_line -= 1
    game_name = data[name_line] \
        .replace("<description>", "") \
        .replace("</description>", "") \
        .replace("\t", "")

    return game_name


def get_fast_match(dat_files, md5hash):
    # Check dat files one by one.
    for dat in dat_files:
        line_number = 0
        game_name = None
        with open("dat/" + dat, "r") as f:
            data = f.readlines()
            for line in data:
                line_number += 1
                # If match found, print every match in this dat file,
                # as sometimes multiple games share the same track.
                # The hope is, that at least one of them will be the
                # actual game in question.
                if md5hash in line:
                    game_name = get_game_name(data, line_number)
                    print_match(md5hash, game_name, dat)
        # Do not check any further dat files to reduce run time.
        if game_name:
            return game_name
    return None


def get_best_match(dat_files, md5hash, file_name):
    best_match_score = 0
    best_name = None

    # Check all dat files
    # TODO: If this turns out to be too slow, it can be parallelised. Alternative similarity algorithms (Levenshtein) are also an option.
    for dat in dat_files:
        line_number = 0
        with open("dat/" + dat, "r") as f:
            data = f.readlines()
            for line in data:
                line_number += 1
                if md5hash in line:
                    game_name = get_game_name(data, line_number)
                    # Get similarity score for the match
                    local_score = SequenceMatcher(None, file_name, game_name).ratio()
                    # The higher the score, the more similar the names
                    if local_score > best_match_score:
                        best_match_score = local_score
                        best_name = game_name
                        # Only print better names, to reduce spam
                        print_match(md5hash, game_name, dat)
    # Return either the best name match, or None
    return best_name


def prepare_path(path_string):
    # Evaluate a raw string, removing any weird single quote escapes created by the terminal
    return ast.literal_eval(path_string.strip().replace(r"'\''", r"\'"))


# --------------------------------------------------------------------------- #
# Check for updates #
with open("dat/_last_update", "r") as f:
    last_update_time = f.read()

if (int(str(datetime.date.today()).split("-")[1]) >
    int(last_update_time.split("-")[1])) \
        | (int(str(datetime.date.today()).split("-")[0]) >
           int(last_update_time.split("-")[0])):
    print("DATs haven't been updated in at least one month")
    i = input("Do you want to update them? (y/n) > ")
    if i == "y":
        exec(open("dat_updater.py").read())
    else:
        pass

# Get file/folder list #
input_list = list()
if len(sys.argv) > 1:
    input_list = sys.argv[1:]
else:
    print(""
          + "============   Redump verifier - version 1.9    ==============\n"
          + "------------       Github.com/normalgamer       --------------\n"
          + "\n"
          + "Drag 'n Drop your ISO or folder\n"
          + "If you want to verify multiple items, separate them by an"
          + "asterisk ( * )\n"
          + "\n"
          )

    userInput = input("> ")
    input_list = userInput.split("*")

# Verify #
for i in input_list:
    path = prepare_path(i)
    if os.path.isfile(path):  # if input is a file
        input_file = list()
        input_file.append(path)
        verify(input_file)

    elif os.path.isdir(path):  # if input is a folder
        inputFiles = get_all_files(path)
        verify(inputFiles)

    else:
        print("Something went wrong...")

print("\n\nSummary:\n")
for rom in romList:
    print(os.path.basename(rom) + " - " +
          romListRedumpName[romList.index(rom)])
    print(romListHash[romList.index(rom)])

input()
