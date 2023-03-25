import imgui
import glfw
import time
import math


class GridEditor:
    def __init__(self):
        self.x = 0
        self.y = 0

    def draw(self, cols, rows, data, coloring=None, minvalue=None, maxvalue=None):
        while len(data) < cols:
            data.append([None]*rows)
        for a in data:
            while len(a) < rows:
                a.append(None)
        if imgui.is_window_focused():
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_LEFT_ARROW)):
                self.x = max(self.x-1, 0)
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_RIGHT_ARROW)):
                self.x = min(self.x+1, 15)
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_UP_ARROW)):
                self.y = max(self.y-1, 0)
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_DOWN_ARROW)):
                self.y = min(self.y+1, 15)
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_DELETE)):
                data[self.x][self.y] = None
            for i in range(10):
                if imgui.is_key_pressed(ord('0')+i):
                    data[self.x][self.y] = i
            for i in range(26):
                if imgui.is_key_pressed(ord('A')+i):
                    data[self.x][self.y] = i+10
            if minvalue is not None:
                data[self.x][self.y] = max(data[self.x][self.y], minvalue)
            if maxvalue is not None:
                data[self.x][self.y] = min(data[self.x][self.y], maxvalue)
        for y in range(rows):
            for x in range(cols):
                imgui.push_id(f"{x}_{y}")
                if x == self.x and y == self.y:
                    if imgui.is_window_focused():
                        t = time.time()
                        imgui.push_style_color(imgui.COLOR_BUTTON, math.sin(t)**2, math.sin(t+2)**2, math.sin(t+4)**2)
                    else:
                        imgui.push_style_color(imgui.COLOR_BUTTON, .3, .3, .3)
                elif coloring is not None:
                    imgui.push_style_color(imgui.COLOR_BUTTON, *coloring(x, y))
                else:
                    imgui.push_style_color(imgui.COLOR_BUTTON, .1, .1, .1)
                if imgui.button(f"{data[x][y] if data[x][y] is not None else '-'}##{x}_{y}"):
                    self.x = x
                    self.y = y
                imgui.pop_style_color()
                if x < cols-1:
                    imgui.same_line()
                imgui.pop_id()


def grid_editor(state, title, width, height):
    imgui.push_id(f"{title}")
    imgui.begin_group()
    io = imgui.get_io()
    s = io.keys_down[glfw.KEY_Q]
    for y in range(height):
        for x in range(width):
            imgui.push_id(f"{x}_{y}")
            draw_list = imgui.get_window_draw_list()
            draw_list.channels_split(2)
            draw_list.channels_set_current(1)
            clicked, _ = imgui.selectable(
                label=f"{x}",
                selected=s,
                flags=0,
                width=20,
                height=20,
            )

            if imgui.is_item_hovered():
                draw_list.channels_set_current(0)
                selectable_color(imgui.get_color_u32_rgba(1, 0, 0, 1))

            draw_list.channels_merge()
            if x < width-1:
                imgui.same_line()
            imgui.pop_id()
    imgui.end_group()
    imgui.pop_id()
