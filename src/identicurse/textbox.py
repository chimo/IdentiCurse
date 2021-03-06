# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2013 Reality <tinmachin3@gmail.com> and Psychedelic Squid <psquid@psquid.net>
# 
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import curses, identicurse, config, helpers, string
from curses import textpad
from curses import ascii

class Textbox(textpad.Textbox):
    def __init__(self, win, poll, insert_mode=False):
        try:
            textpad.Textbox.__init__(self, win, insert_mode)
        except TypeError:  # python 2.5 didn't support insert_mode
            textpad.Textbox.__init__(self, win)
        self.poll_function = poll

    def edit(self, initial_input=""):
        old_curs_state = 0

        try:
            old_curs_state = curses.curs_set(1)
        except:
            pass

        for char in list(initial_input):
            self.do_command(ord(char))
        self.poll_function(self.count())

        abort = False
        while 1:
            insert = False
            ch = self.win.getch()
            
            if ch == curses.ascii.DEL:
                self.do_command(curses.ascii.BS)
            elif ch == curses.KEY_ENTER or ch == 10:
                break
            elif ch == curses.ascii.ESC:
                abort = True
                break
            elif ch == curses.ascii.TAB:
                cursor_position = self.win.getyx()
                x = cursor_position[1]
                last_word = ""
                while True:
                    x -= 1
                    c = chr(curses.ascii.ascii(self.win.inch(cursor_position[0], x)))
                    if c == " ":
                        if (len(last_word) == 0) and (x > 0):
                            continue
                        else:
                            break
                    last_word = c + last_word
                    if x == 0:
                        break
                self.win.move(cursor_position[0], cursor_position[1])
                guess_source = None
                if helpers.url_regex.match(last_word):  # this is a URL, shorten it
                    shorturl = helpers.ur1ca_shorten(last_word)
                    for n in xrange(len(last_word)):
                        self.win.move(self.win.getyx()[0], self.win.getyx()[1]-1)
                        self.delch()
                    for char in shorturl:
                        self.do_command(ord(char))
                elif last_word[0] == "@" and hasattr(config.session_store, "user_cache"):
                    last_word = last_word[1:]
                    guess_source = getattr(config.session_store, "user_cache")
                elif last_word[0] == "!" and hasattr(config.session_store, "group_cache"):
                    last_word = last_word[1:]
                    guess_source = getattr(config.session_store, "group_cache")
                elif last_word[0] == "#" and hasattr(config.session_store, "tag_cache"):
                    last_word = last_word[1:]
                    guess_source = getattr(config.session_store, "tag_cache")
                elif last_word[0] == "/" and hasattr(config.session_store, "commands"):
                    last_word = last_word[1:]
                    guess_source = getattr(config.session_store, "commands")
                elif hasattr(config.session_store, "user_cache"):  # if no special char, assume username
                    guess_source = getattr(config.session_store, "user_cache")
                if guess_source is not None:
                    if config.config["tab_complete_mode"] == "exact":
                        possible_guesses = [user for user in guess_source if user[:len(last_word)] == last_word]
                        guess = helpers.find_longest_common_start(possible_guesses)
                        if len(guess) > len(last_word):
                            for char in guess[len(last_word):]:
                                self.do_command(ord(char))
                        elif len(possible_guesses) > 0:
                            self.poll_function(possible_guesses)
                    else:
                        possible_guesses = helpers.find_fuzzy_matches(last_word, guess_source)
                        common_guess = helpers.find_longest_common_start(possible_guesses)
                        if len(common_guess) != 0 and len(helpers.find_fuzzy_matches(last_word, [common_guess,])) > 0:
                            self.win.move(self.win.getyx()[0], self.win.getyx()[1]-len(last_word))
                            for i in xrange(len(last_word)):
                                self.delch()
                            for char in common_guess:
                                self.do_command(ord(char))
                        if len(possible_guesses) >= 2:
                            self.poll_function(possible_guesses)
            elif ch == curses.KEY_HOME:
                self.win.move(0, 0)
            elif ch == curses.KEY_END:
                for y in range(self.maxy+1):
                    if y == self.maxy:
                        self.win.move(y, self._end_of_line(y))
                        break
                    if self._end_of_line(y+1) == 0:
                        self.win.move(y, self._end_of_line(y))
                        break
            elif ch == curses.KEY_BACKSPACE or ch == curses.ascii.ctrl(ord("h")):
                cursor_y, cursor_x = self.win.getyx()
                if cursor_x == 0:
                    if cursor_y == 0:
                        continue
                    else:
                        self.win.move(cursor_y - 1, self.maxx)
                else:
                    self.win.move(cursor_y, cursor_x - 1)
                self.delch()
            elif ch == curses.KEY_DC or ch == curses.ascii.ctrl(ord("d")):
                self.delch()
            elif ch == curses.ascii.ctrl(ord("u")):  # delete entire line up to the cursor
                cursor_y, cursor_x = self.win.getyx()
                self.win.move(cursor_y, 0)
                for char_count in xrange(0, cursor_x):
                    self.delch()
            elif ch == curses.ascii.ctrl(ord("w")):  # delete all characters before the current one until the beginning of the word
                cursor_y, cursor_x = self.win.getyx()
                x, y = cursor_x, cursor_y
                only_spaces_so_far = True
                while True:
                    if x == 0:
                        if y == 0:
                            break
                        else:
                            y -= 1
                            x = self.maxx
                    else:
                        x -= 1
                    if curses.ascii.ascii(self.win.inch(y, x)) != ord(" "):
                        self.win.move(y, x)
                        self.delch()
                        only_spaces_so_far = False
                    else:
                        if only_spaces_so_far:
                            self.win.move(y, x)
                            self.delch()
                        else:
                            if x == self.maxx:
                                self.win.move(y + 1, 0)
                            else:
                                self.win.move(y, x + 1)
                            break
            elif ch > 127 and ch <= 256:
                cursor_y, cursor_x = self.win.getyx()

                if cursor_y < self.maxy:
                    overhang_ch = self.win.inch(cursor_y, self.maxx)
                    if overhang_ch <= 127:
                        self.win.insch(cursor_y+1, 0, overhang_ch)
                    elif overhang_ch <= 256:
                        for c in self.unicode_demangle(overhang_ch):
                            self.win.insch(cursor_y+1, 0, ord(c))

                for c in self.unicode_demangle(ch):
                    self.win.insch(cursor_y, cursor_x, ord(c))

                if cursor_x < self.maxx:
                    self.win.move(cursor_y, cursor_x+1)
                elif cursor_y < self.maxy:
                    self.win.move(cursor_y+1, 0)

            elif ch <= 127 and chr(ch) in string.printable:
                cursor_y, cursor_x = self.win.getyx()
                if cursor_y < self.maxy:
                    overhang_ch = self.win.inch(cursor_y, self.maxx)
                    if overhang_ch <= 127:
                        self.win.insch(cursor_y+1, 0, overhang_ch)
                    elif overhang_ch <= 256:
                        for c in self.unicode_demangle(overhang_ch):
                            self.win.insch(cursor_y+1, 0, ord(c))

                self.win.insch(cursor_y, cursor_x, ch)

                if cursor_x < self.maxx:
                    self.win.move(cursor_y, cursor_x+1)
                elif cursor_y < self.maxy:
                    self.win.move(cursor_y+1, 0)
            elif not ch:
                continue
            elif not self.do_command(ch):
                break

            self.poll_function(self.count())
            self.win.refresh()

        try:
            curses.curs_set(old_curs_state)  # try to restore the cursor's state before returning to normal operation
        except:
            pass
        if abort == False:
            return self.gather()
        else:
            self.win.clear()
            self.win.refresh()
            return None

    def unicode_demangle(self, unicode_ch):
        #liberated from http://groups.google.com/group/comp.lang.python/browse_thread/thread/67dce30f0a2742a6?fwc=2&pli=1
        def check_next_byte():
            unicode_ch = self.win.getch()
            if 128 <= unicode_ch <= 191:
                return unicode_ch
            else:
                raise UnicodeError

        bytes = []
        bytes.append(unicode_ch)
        if 194 <= unicode_ch <= 223:
            #2 bytes
            bytes.append(check_next_byte())
        elif 224 <= unicode_ch <= 239:
            #3 bytes
            bytes.append(check_next_byte())
            bytes.append(check_next_byte())
        elif 240 <= unicode_ch <= 244:
            #4 bytes
            bytes.append(check_next_byte())
            bytes.append(check_next_byte())
            bytes.append(check_next_byte())

        return "".join([chr(b) for b in bytes])

    def delch(self):  # delch, but with provisions for moving characters across lines
        cursor_y, cursor_x = self.win.getyx()
        self.win.delch()
        if cursor_y < self.maxy:
            for line_offset in xrange(0, self.maxy - cursor_y):
                self.win.insch(cursor_y + line_offset, self.maxx, curses.ascii.ascii(self.win.inch(cursor_y + line_offset + 1, 0)))
                self.win.delch(cursor_y + line_offset + 1, 0)
            self.win.move(cursor_y, cursor_x)

    def gather_only(self):
        "Collect and return the contents of the window."
        cursor_position = self.win.getyx()
        result = [""]
        for y in range(self.maxy+1):
            self.win.move(y, 0)
            stop = self._end_of_line(y)
            if stop == 0 and self.stripspaces:
                continue
            for x in range(self.maxx+1):
                if self.stripspaces and x > stop:
                    result.append("")
                    break

                # deal with non-ascii
                char = self.win.inch(y, x)
                if char == curses.ascii.ascii(char):
                    char = chr(curses.ascii.ascii(char))
                else:
                    char = '&#%u;' % char

                if char == " ":
                    result.append("")
                else:
                    result[-1] += char
        result = [word for word in result if word != ""]
        self.win.move(*cursor_position)
        return " ".join(result)

    def gather(self):
        "Return the contents of the window, and also clear it. Explicitly use gather_only() if you need to preserve the contents."
        result = self.gather_only()
        self.win.clear()
        self.win.refresh()
        return result

    def count(self):
        cursor_position = self.win.getyx()
        count = 0
        for y in range(self.maxy+1):
            self.win.move(y, 0)
            if (y == cursor_position[0]) and (cursor_position[1] > self._end_of_line(y)):
                stop = cursor_position[1]
            else:
                stop = self._end_of_line(y)
            if stop != 0:
                count -= 1
            else:
                break
            for x in range(self.maxx+1):
                if self.stripspaces and x > stop:
                    break
                count += 1
            count += 1
        self.win.move(cursor_position[0], cursor_position[1])
        return count
