import imgui
import glfw
import time
import math


COLUMN_WIDTH = 20


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
                self.x = min(self.x+1, cols-1)
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_UP_ARROW)):
                self.y = max(self.y-1, 0)
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_DOWN_ARROW)):
                self.y = min(self.y+1, rows-1)
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_PAGE_UP)):
                data[self.x][self.y] = (data[self.x][self.y] or 0) + 1
            if imgui.is_key_pressed(imgui.get_key_index(imgui.KEY_PAGE_DOWN)):
                data[self.x][self.y] = (data[self.x][self.y] or 0) - 1
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
        for x in range(cols):
            imgui.button(f"{x}##title_{x}", width=COLUMN_WIDTH)
            if x < cols-1:
                imgui.same_line()
        for y in range(rows):
            for x in range(cols):
                imgui.push_id(f"{x}_{y}")
                color = None
                if x == self.x and y == self.y:
                    if imgui.is_window_focused():
                        t = time.time()
                        color = (math.sin(t)**2, math.sin(t+2)**2, math.sin(t+4)**2)
                    else:
                        color = (.3, .3, .3)
                elif coloring is not None:
                    color = coloring(x, y)
                if color is None:
                    color = (.1, .1, .1)
                imgui.push_style_color(imgui.COLOR_BUTTON, color[0], color[1], color[2])
                if imgui.button(f"{data[x][y] if data[x][y] is not None else '-'}##{x}_{y}", width=COLUMN_WIDTH):
                    self.x = x
                    self.y = y
                imgui.pop_style_color()
                if x < cols-1:
                    imgui.same_line()
                imgui.pop_id()
