import rtmidi


class Midi():
    def __init__(self):
        self.midiout = rtmidi.MidiOut()

    def __enter__(self):
        self.midiout.open_port(0)
        self.midiout.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self.midiout.__exit__(type, value, traceback)

    def set_instrument(self, channel, instrument):
        msg = [0xC0 + channel, instrument, 0]
        self.midiout.send_message(msg)

    def note_on(self, channel, note, velocity):
        msg = [0x90 + channel, note, velocity]
        self.midiout.send_message(msg)

    def channel_notes_off(self, channel):
        msg = [0xB0 + channel, 0x7B, 0]
        self.midiout.send_message(msg)

    def all_notes_off(self):
        for i in range(16):
            self.channel_notes_off(i)
