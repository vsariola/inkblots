import threading
import time
from typing import Optional
import imgui
import midi
import widgets
import math
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, DataClassJsonMixin

from ptimer import repeat

NUM_CHANNELS = 4


@dataclass_json()
@dataclass()
class Channel(DataClassJsonMixin):
    instrument: int = 0
    volume: int = 127
    duration: int = 4
    octave: int = 0


@dataclass_json()
@dataclass()
class Song(DataClassJsonMixin):
    channels: list[Channel] = field(default_factory=lambda: [Channel() for _ in range(NUM_CHANNELS)])
    bpm: int = 120
    pattern_length: int = 8
    pattern_repeats: int = 4
    order_list_length: int = 8
    chord_pattern_length: int = 4
    chord_duration: int = 4
    mode: int = 1
    order_list: list[list[Optional[int]]] = field(default_factory=lambda: [])
    patterns: list[list[Optional[int]]] = field(default_factory=lambda: [])
    chords: list[list[Optional[int]]] = field(default_factory=lambda: [])

    @property
    def ticks_per_order_row(self):
        return self.pattern_repeats * self.pattern_length * 4

    @property
    def ticks_per_chord_row(self):
        return self.pattern_repeats * self.pattern_length * self.chord_duration


class Tracker:
    def __init__(self, path):
        self.midi = midi.Midi()
        self.path = path
        self.playing = False
        self.t = 0
        self.closed = False
        self.order_list_editor = widgets.GridEditor()
        self.patterns_editor = widgets.GridEditor()
        self.chords_editor = widgets.GridEditor()
        try:
            with open(self.path, "r") as infile:
                s = infile.read()
                self.song = Song.from_json(s)
        except:
            self.song = Song()
        threading.Timer(0, self.interrupt).start()
        self.autosave()

    def __enter__(self):
        self.midi.__enter__()
        for i in range(NUM_CHANNELS):
            self.midi.set_instrument(i + 9, self.song.channels[i].instrument)
        return self

    def __exit__(self, type, value, traceback):
        self.save()
        self.midi.__exit__(type, value, traceback)
        self.closed = True

    def autosave(self):
        if self.closed:
            return
        threading.Timer(5, self.autosave).start()
        threading.Thread(target=self.save).start()

    def save(self):
        try:
            with open(self.path, "w") as outfile:
                outfile.write(self.song.to_json())
        except:
            pass

    def draw(self):
        self.draw_channels()
        self.draw_song()
        self.draw_order_list()
        self.draw_patterns()
        self.draw_chords()

    def draw_channels(self):
        imgui.begin("Channels")
        imgui.begin_group()
        imgui.text("Instrument")
        imgui.text("Octave")
        imgui.text("Duration")
        imgui.text("Volume")
        imgui.end_group()
        imgui.same_line()
        for i in range(NUM_CHANNELS):
            self.draw_channel(i)
        imgui.end()

    def draw_channel(self, i):
        imgui.push_id(f"channel_{i}")
        imgui.begin_group()
        imgui.push_item_width(100)
        chn = self.song.channels[i]
        changed, chn.instrument = imgui.input_int(f"###instrument_{i}", chn.instrument)
        chn.instrument = min(max(chn.instrument, 0), 255)
        if changed:
            self.midi.set_instrument(i + 9, chn.instrument)
        changed, chn.octave = imgui.input_int(f"###octave_{i}", chn.octave)
        chn.octave = min(max(chn.octave, 0), 8)
        changed, chn.duration = imgui.input_int(f"###chnduration_{i}", chn.duration)
        chn.duration = min(max(chn.duration, 0), 16)
        changed, chn.volume = imgui.slider_int(f"###chnvolume{i}", chn.volume, 0, 127)
        imgui.pop_item_width()
        imgui.end_group()
        imgui.same_line()
        imgui.pop_id()

    def my_input_int(self, title, name, minvalue=None, maxvalue=None):
        val = getattr(self.song, name)
        ret, val = imgui.input_int(title, val)
        if minvalue is not None:
            val = max(val, minvalue)
        if maxvalue is not None:
            val = min(val, maxvalue)
        setattr(self.song, name, val)

    def draw_song(self):
        imgui.begin("Song")
        if imgui.button("Play"):
            self.playing = True
        if imgui.button("Stop"):
            self.playing = False
        imgui.push_item_width(100)
        self.my_input_int("BPM", "bpm", 1, 999)
        self.my_input_int("Ordlen", "order_list_length", 1, 999)
        self.my_input_int("Patlen", "pattern_length", 1, 32)
        self.my_input_int("Patreps", "pattern_repeats", 1, 16)
        self.my_input_int("Chordlen", "chord_pattern_length", 1, 32)
        self.my_input_int("Chorddur", "chord_duration", 1, 32)
        self.my_input_int("Mode", "mode", 0, 6)
        imgui.pop_item_width()
        imgui.end()

    def draw_order_list(self):
        imgui.begin("Order list")
        def coloring(x, y): return channel_color(x) if self.playing and y == self.order_list_play_row else None
        self.order_list_editor.draw(5, self.song.order_list_length, self.song.order_list, coloring=coloring)
        if imgui.is_window_focused():
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_ENTER)):
                self.toggle_playing()
                if self.playing:
                    self.t = self.order_list_editor.y * self.song.ticks_per_order_row
        imgui.end()

    def toggle_playing(self):
        self.playing = not self.playing
        if not self.playing:
            self.midi.all_notes_off()

    def draw_patterns(self):
        imgui.begin("Patterns")
        self.patterns_editor.draw(16, self.song.pattern_length, self.song.patterns)
        imgui.end()

    def draw_chords(self):
        imgui.begin("Chord progressions")
        self.chords_editor.draw(16, self.song.chord_pattern_length, self.song.chords, coloring=lambda x, y: channel_color(0)
                                if self.playing and x == self.chord_play_column and y == self.chord_play_row else None)
        imgui.end()

    def get_interrupt_interval(self):
        return 60 / (self.song.bpm * 4)

    def interrupt(self):
        if self.closed:
            return
        interval = self.get_interrupt_interval()
        delay = interval - (time.time() % interval)
        threading.Timer(delay,
                        self.interrupt).start()
        if self.playing:
            threading.Thread(target=self.sound).start()

    @property
    def order_list_play_row(self):
        return self.t // self.song.ticks_per_order_row

    @property
    def chord_play_row(self):
        return self.t // self.song.ticks_per_chord_row % self.song.chord_pattern_length

    @property
    def chord_play_column(self):
        try:
            return self.song.order_list[0][self.order_list_play_row]
        except:
            return None

    @property
    def chord_play_value(self):
        try:
            ret = self.song.chords[self.chord_play_column][self.chord_play_row]
        except:
            ret = 0
        return ret if ret is not None else 0

    def pattern_play_column(self, chnindex):
        try:
            return self.song.order_list[chnindex + 1][self.order_list_play_row]
        except:
            return None

    def pattern_play_row(self, chnindex):
        try:
            return self.t // self.song.channels[chnindex].duration % self.song.pattern_length
        except:
            return None

    def pattern_play_value(self, chnindex):
        try:
            return self.song.patterns[self.pattern_play_column(chnindex)][self.pattern_play_row(chnindex)]
        except IndexError:
            return None

    def sound(self):
        for i in range(NUM_CHANNELS):
            try:
                if self.t % self.song.channels[i].duration == 0:
                    n = self.pattern_play_value(i)
                    # self.midi.all_notes_off(i)
                    if n is not None:
                        self.midi.channel_notes_off(i + 9)
                        if i > 0:
                            n = (n + self.song.mode + self.chord_play_value) * 12 // 7
                            n += 12 * self.song.channels[i].octave
                        else:
                            n += 25
                        self.midi.note_on(i + 9, n, self.song.channels[i].volume)
            except:
                continue
        self.t += 1


def channel_color(i):
    return (math.sin(i) * .5 + .5, math.sin(i + 2) * .5 + .5, math.sin(i + 4) * .5 + .5)
