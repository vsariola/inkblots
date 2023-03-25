import threading
import time
import imgui
import midi
import widgets
import math
import json

from ptimer import repeat

NUM_CHANNELS = 4
AUTOSAVEFILE = 'songdata.pk'


class Tracker:
    def __init__(self):
        self.midi = midi.Midi()

        def foo():
            self.foo()
        # self.timer = repeat(self.foo, interval=1)
        self.instruments = [0]*NUM_CHANNELS
        self.octaves = [0]*NUM_CHANNELS
        self.data = [[None]*16 for i in range(16)]
        self.instr_duration = [1] * NUM_CHANNELS
        self.bpm = 120  # PIT Hz = 1.1931816666e6 / divisor, where divisor = 1..65536 (65536 => 18.2 Hz)
        self.patlen = 8
        self.patreps = 4
        self.ordlen = 8
        self.chordlen = 4
        self.chord_duration = 4
        self.mode = 0
        self.order_list = []
        self.patterns = []
        self.chords = []
        self.playing = False
        self.t = 0
        self.order_list_editor = widgets.GridEditor()
        self.patterns_editor = widgets.GridEditor()
        self.chords_editor = widgets.GridEditor()
        threading.Timer(0, self.interrupt).start()

    def __enter__(self):
        self.midi.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self.midi.__exit__(type, value, traceback)

    def draw(self):
        self.draw_instruments()
        self.draw_song()
        self.draw_order_list()
        self.draw_patterns()
        self.draw_chords()

    def foo(self):
        self.midi.note_on(0, 20, 127)

    def draw_instruments(self):
        imgui.begin("Channels")
        imgui.columns(1 + NUM_CHANNELS)
        imgui.text("Instrument")
        imgui.next_column()
        for i in range(NUM_CHANNELS):
            changed, self.instruments[i] = imgui.input_int(f"###instr_{i}", self.instruments[i])
            self.instruments[i] = min(max(self.instruments[i], 0), 255)
            if changed:
                self.midi.set_instrument(i, self.instruments[i])
            imgui.next_column()
        imgui.text("Octave")
        imgui.next_column()
        for i in range(NUM_CHANNELS):
            changed, self.octaves[i] = imgui.input_int(f"###oct_{i}", self.octaves[i])
            self.octaves[i] = min(max(self.octaves[i], 0), 8)
            imgui.next_column()
        imgui.text("Note duration")
        imgui.next_column()
        for i in range(NUM_CHANNELS):
            changed, self.instr_duration[i] = imgui.input_int(f"###notedur_{i}", self.instr_duration[i])
            self.instr_duration[i] = min(max(self.instr_duration[i], 0), 8)
            imgui.next_column()
        imgui.columns(1)
        imgui.end()

    def draw_song(self):
        imgui.begin("Song")
        if imgui.button("Play"):
            self.playing = True
        if imgui.button("Stop"):
            self.playing = False
        imgui.push_item_width(100)
        _, self.bpm = imgui.input_int(f"BPM", self.bpm)
        self.bpm = min(max(self.bpm, 1), 999)
        _, self.ordlen = imgui.input_int(f"Ordlen", self.ordlen)
        self.ordlen = min(max(self.ordlen, 1), 32)
        _, self.patlen = imgui.input_int(f"Patlen", self.patlen)
        self.patlen = min(max(self.patlen, 1), 32)
        _, self.patreps = imgui.input_int(f"Patreps", self.patreps)
        self.patreps = min(max(self.patreps, 1), 32)
        _, self.chordlen = imgui.input_int(f"Chordlen", self.chordlen)
        self.chordlen = min(max(self.chordlen, 1), 32)
        _, self.chord_duration = imgui.input_int(f"Chord dur", self.chord_duration)
        self.chord_duration = min(max(self.chord_duration, 1), 16)
        _, self.mode = imgui.input_int(f"Mode", self.mode)
        self.mode = min(max(self.mode, 0), 6)
        imgui.pop_item_width()
        imgui.end()

    def draw_order_list(self):
        imgui.begin("Order list")
        self.order_list_editor.draw(5, self.ordlen, self.order_list, coloring=lambda x, y: channel_color(x) if self.playing and y == self.ordrow() else None)
        if imgui.is_window_focused():
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_ENTER)):
                if self.playing:
                    self.playing = False
                else:
                    self.playing = True
                    self.t = self.patdur() * self.order_list_editor.y
        imgui.end()

    def draw_patterns(self):
        imgui.begin("Patterns")
        self.patterns_editor.draw(16, self.patlen, self.patterns)
        imgui.end()

    def draw_chords(self):
        imgui.begin("Chord progressions")
        self.chords_editor.draw(16, self.chordlen, self.chords, coloring=lambda x, y: channel_color(0) if self.playing and x == self.chordcolumn() and y == self.chordrow() else None)
        imgui.end()

    def get_interrupt_interval(self):
        return 60 / (self.bpm * 4)

    def interrupt(self):
        interval = self.get_interrupt_interval()
        delay = interval - (time.time() % interval)
        threading.Timer(delay,
                        self.interrupt).start()
        if self.playing:
            threading.Thread(target=self.sound).start()

    def patdur(self):
        return self.patreps * self.patlen * 4

    def ordrow(self):
        return self.t // self.patdur()

    def chnrow(self, i):
        return self.t // self.instr_duration[i] % self.patlen

    def chordrow(self):
        return self.t // (self.chord_duration * 4) % self.chordlen

    def chordcolumn(self):
        return self.order_list[0][self.ordrow()] or 0

    def sound(self):
        o = self.ordrow()
        cr = self.chordrow()
        cp = self.chordcolumn()
        chord = self.chords[cp][cr] or 0
        for i in range(NUM_CHANNELS):
            try:
                if self.t % self.instr_duration[i] == 0:
                    p = self.order_list[i+1][o]
                    r = self.chnrow(i)
                    n = self.patterns[p][r]
                    self.midi.all_notes_off(i)
                    if n is not None:
                        n = (n + self.mode + chord) * 12 // 7
                        n += 12 * self.octaves[i]
                        self.midi.note_on(i, n, 127)
            except:
                continue
        self.t += 1


class TrackerEncoder(json.JSONEncoder):
    def default(self, obj):
        return {

        }


def channel_color(i):
    return (math.sin(i)*.5+.5, math.sin(i+2)*.5+.5, math.sin(i+4)*.5+.5)
