import tracker


def main():
    with open("autosave.json", "r") as infile:
        s = infile.read()
        song = tracker.Song.from_json(s)
