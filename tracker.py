import imgui
import midi
import widgets
from ptimer import repeat

NUM_CHANNELS = 4


class Tracker:
    def __init__(self):
        self.midi = midi.Midi()

        def foo():
            self.foo()
        # self.timer = repeat(self.foo, interval=1)
        self.instruments = [0]*NUM_CHANNELS
        self.octaves = [0]*NUM_CHANNELS
        self.data = [[None]*16 for i in range(16)]
        self.instr_duration = [0] * NUM_CHANNELS
        self.x = 0
        self.y = 0
        self.bpm = 120  # PIT Hz = 1.1931816666e6 / divisor, where divisor = 1..65536 (65536 => 18.2 Hz)
        self.patlen = 8
        self.patreps = 4
        self.ordlen = 8
        self.chordlen = 8
        self.order_list = []
        self.patterns = []
        self.chords = []
        self.order_list_editor = widgets.GridEditor()
        self.patterns_editor = widgets.GridEditor()
        self.chords_editor = widgets.GridEditor()

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

    def selectable_color(self, color):
        p_min = imgui.get_item_rect_min()
        p_max = imgui.get_item_rect_max()
        imgui.get_window_draw_list().add_rect_filled(p_min[0], p_min[1], p_max[0], p_max[1], color)

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
        imgui.pop_item_width()
        imgui.end()

    def draw_order_list(self):
        imgui.begin("Order list")
        self.order_list_editor.draw(5, self.ordlen, self.order_list)
        imgui.end()

    def draw_patterns(self):
        imgui.begin("Patterns")
        self.patterns_editor.draw(16, self.patlen, self.patterns)
        imgui.end()

    def draw_chords(self):
        imgui.begin("Chord progressions")
        self.chords_editor.draw(16, self.chordlen, self.chords)
        imgui.end()

    def sound():
        pass
