"""
Gimmick module API version: 1.6

Classes to abstract away BMS for making gimmick charts...
Produces big BMS files very slowly.
Make sure to parse measures in order if you inserting new measures!

Example:
o = BMSparser('input.bme')
# (do stuff)
o.optimize()
o.write_output('output.bme')
"""


class LLNode:
    """
    Linked list node
    """

    def __init__(self, v, nextNode=None):
        """
        :param v: Value
        :type v: object
        :param nextNode: Next node in list
        :type nextNode: LLNode | None
        """
        self.value = v
        self.next = nextNode

    def __repr__(self):
        return "LLNode(" + repr(self.value) + ")"


class LLError(Exception):
    pass


class LL:
    """
    Imagine actually using a LL for anything

    # Use a LL data structure to provide easily re-index-able insertion/deletion.
    # Uses numerical keys only.
    # We use this instead of dicts for single mes:value pairs.
    """

    def __init__(self):
        self.len = 0
        self.start = None
        self.end = None

    def _traverse(self, index):
        if self.start is None:
            raise LLError('Empty LL')
        cur = self.start
        for i in range(index):
            cur = cur.next
        return cur

    def __getitem__(self, index):
        if index < 0:
            raise LLError('Negative index')
        if index > self.len:
            raise LLError('Attempted to access index past end')
        n = self._traverse(index)
        if n.value is None:
            raise LLError('Empty node')
        return n.value

    def __setitem__(self, index, value):
        if index < 0:
            raise LLError('Negative index')
        if index >= self.len:
            if self.len == 0:
                bn = LLNode(None)
                self.len = 1
                self.start = bn
            else:
                bn = self.end
            for i in range(index - self.len + 1):
                bn.next = LLNode(None)
                bn = bn.next
            self.len = index + 1
            self.end = bn
        else:
            bn = self._traverse(index)
        bn.value = value

    def __contains__(self, item):
        return self.len > item >= 0 and (self._traverse(item).value is not None)

    def append(self, index, value):
        """
        Append a value at index, shifting next

        :param index: Index
        :type index: int
        :param value: Value
        :type value: object
        :rtype: None
        """

        if self.len == 0 or index >= self.len:
            self[index] = value  # just shove it in
        n = self._traverse(index - 1)
        nn = n.next
        n.next = LLNode(value)
        self.len += 1
        n.next.next = nn

    def shift_start(self, index):
        """
        Add value empty items to the start

        :param index: Index
        :type index: int
        :rtype: None
        """
        for _ in range(index):
            nn = LLNode(None)
            nn.next = self.start
            self.start = nn

    def items(self):
        if self.len == 0:
            return []

        def ll_iter_items():
            cur = self.start
            i = 0
            if self.start.value is not None:
                yield i, self.start.value
            while cur.next is not None:
                cur = cur.next
                i += 1
                if cur.value is not None:
                    yield i, cur.value
            raise StopIteration()

        return ll_iter_items()

    def values(self):
        if self.len == 0:
            return []

        def ll_iter_values():
            cur = self.start
            if self.start.value is not None:
                yield self.start.value
            while cur.next is not None:
                cur = cur.next
                if cur.value is not None:
                    yield cur.value
            raise StopIteration()

        return ll_iter_values()


class Note:
    """
    Represents a single note
    Also contains static attributes with lane numbers
    """
    LANE_BGM = '01'
    LANE_BPM = '08'
    LANE_STOP = '09'
    LANES_BGA = ('04', '06', '07', '0A')
    LANES_VISIBLE = ('11', '12', '13', '14', '15', '16', '18', '19')
    LANES_LN = ('51', '52', '53', '54', '55', '56', '58', '59')

    @staticmethod
    def clone(newNote):
        """
        Get a copy of a Note

        :param newNote: The note to clone
        :type newNote: Note
        :rtype: Note
        """
        return Note(newNote.object, newNote.pos, newNote.lane, newNote.size)

    def __init__(self, sound, position, lane=None, size=None):
        """
        Create a new note
        Lane and size here do NOT reflect in output

        :param sound: The sound object 00-ZZ
        :type sound: str
        :param position: The position in the measure
        :type position: int
        :param lane: Optional lane where the note is - redundant
        :type lane: str
        :param size: Optional size of the measure where the note is - redundant
        :type size: int
        """
        self.object = sound
        self.pos = position
        self.lane = lane
        self.size = size

    def __repr__(self):
        return "Note(%s, %s, %s)" % (self.object, self.pos, self.lane)


class Measure:
    """
    Represents a single measure.

    Note that one lane/measure combo can have multiple Measure objects corresponding to it.
    They will be combined if possible like standard BMS,
    but an error will be thrown if you have two objects at the same position in non-BGM lanes.
    """
    DP_MINE = False  # Set this to true to force all mines to be moved to the DP side.

    def __init__(self, size, lane, number, meter=None):
        """
        Meter does NOT reflect in output, use BMSparser.meters
        The size of a measure should be a whole number, and if it's not an integer it will be converted here.

        :param size: Size of the measure (i.e. 16)
        :type size: int | float
        :param lane: Lane of the measure (i.e. '11')
        :type lane: str
        :param number: Number of the measure
        :type number: int
        :param meter: UNUSED
        :type meter: float
        """

        if size % 1 != 0:
            raise ValueError("Invalid size %s" % size)
        self.base_meter = meter
        self.meter = meter  # Possible feature: auto convert when changed from base?
        self.number = number
        self.size = int(size)
        self.lane = lane if (lane[0] != 'D' or not self.DP_MINE) else ('E' + lane[1])
        self.notes = []

    def get_string(self, mes=None):
        """
        Return a valid BMS line representation of the measure

        :param mes: Number of the measure, defaults to defined
        :type mes: int
        :return: Single line representing measure
        :returns: str
        """
        if mes is None:
            mes = self.number
        base_str = '#' + '%03d' % mes + self.lane + ':'
        notes = ['00'] * self.size
        try:
            for n in self.notes:
                if n.pos < 0:
                    raise IndexError
                notes[n.pos] = n.object
        except IndexError:
            print('---- ERROR ----')
            print('There was a note out of range!')
            print(self)
            raise IndexError
        return base_str + ''.join(notes)

    def add(self, note):
        """
        Add a note to the measure. Validates that all notes are in unique positions.
        If you want multiple BGM notes at the same place, make another Measure object.
        The BMSparser.optimize method will get rid of most excess measure lines.

        :param note: Note to add
        :type note: Note
        :rtype: None
        """
        if not all(n.pos != note.pos for n in self.notes):
            raise ValueError('Duplicate note position in single measure not currently supported')
        self.notes.append(note)

    def contains_pos(self, i):
        """
        Returns true if there is a note with position i in the measure.

        :param i: Position to check
        :type i: int
        :rtype: bool
        """
        return any(m.pos == i for m in self.notes)

    @staticmethod
    def clone(newMes):
        """
        Get a copy of a measure object

        :param newMes: Measure to copy
        :type newMes: Measure
        :rtype: Measure
        """
        n = Measure(newMes.size, newMes.lane, newMes.number, newMes.meter)
        n.notes = [Note.clone(note) for note in newMes.notes]
        return n

    def __repr__(self):
        return "Measure(size=%s, lane='%s', number=%s, meter=%s), Notes [\n\t" % \
               (self.size, self.lane, self.number, self.meter) + "\n\t".join(
                repr(n) for n in self.notes) + "\n]"


class BMSparser:
    """
    Class to parse BMS files.
    """
    from numpy import lcm, base_repr
    VERSION = '1.6'

    def __init__(self, name, enc='cp932', allow_unsafe=False):
        """
        Load a BMS from a file. The default encoding is Shift-JIS.

        :param name: The name of the file to load
        :type name: str
        :param enc: The encoding to load the file with
        :type enc: str
        :param allow_unsafe: Allow things that may not work with LR2 (currently only high BPMs)
        :type allow_unsafe: bool
        """
        self.measures = []
        self.stop_objects = {}  # key/value length/index
        self.stop_index = 1
        self.stop_measures = LL()  # key/value mes/measure
        self.bpm_objects = {}  # key/value bpm/index
        self.bpm_index = 10  # bug might require starting at 10...?
        self.bpm_measures = LL()  # key/value mes/measure
        self.meters = LL()  # key/value measure/meter
        self.ignored_lines = []
        self.mine_damage = '01'
        self.keysounds = {}
        self.allow_unsafe = allow_unsafe
        # Dict of list of Measure objects per measure.
        # Allowing multiple lets us split up polyrhythms without making excessively long lines.
        # For now we just make a new measure object per line since it's easy.
        # We can also split up STOP lines and so on the same way.
        self.__parse(name, enc)

    def __parse(self, name, enc):
        """
        This should not need to be called explicitly.
        For internal usage.

        TODO handle bpm objects properly (>=10)
        """
        for line in open(name, 'r', encoding=enc):
            if line[0] == '#' and line[1].isnumeric():
                mi = int(line[1:4])
                if line[4:6] == '02':
                    self.meters[mi] = float(line[7:])
                    continue
                m = Measure((len(line) - 8) / 2, line[4:6], mi, self.meters[mi] if mi in self.meters else 1)
                [m.add(Note(line[7 + i * 2:9 + i * 2], i, line[4:6], (len(line) - 8) // 2)) for i in
                 range((len(line) - 8) // 2) if line[7 + i * 2:9 + i * 2] != '00']
                self.measures.append(m)
            elif line.startswith("#WAV"):
                self.keysounds[line[4:6]] = line[7:-1]
            elif line.startswith("#BPM") and line[4] != ' ':  # TODO 03 BPMs not handled RN
                self.bpm_objects[float(line[7:])] = line[4:6]
            elif line.startswith("#STOP"):
                self.stop_objects[int(line[8:])] = line[5:7]
            elif line != '\n':
                self.ignored_lines.append(line)
        self.stop_index = max(1, len(self.stop_objects) + 1)
        self.bpm_index = max(10, len(self.bpm_objects) + 1)

    def _stop_index(self, length):
        """
        Returns the value to use of the stop object corresponding to the stop length.

        :param length: Stop length
        :type length: int
        :rtype: str
        """
        if length in self.stop_objects:
            return self.stop_objects[length]
        if self.stop_index >= 1296:
            raise ValueError("Cannot use any more stops!")
        self.stop_objects[length] = BMSparser.base_repr(self.stop_index, 36).rjust(2, '0')
        self.stop_index += 1
        return self.stop_objects[length]

    def _bpm_index(self, length):
        """
        Returns the value to use of the BPM object corresponding to the BPM.

        :param length: BPM
        :type length: int
        :rtype: str
        """
        if not self.allow_unsafe and length >= 16777216:
            raise ValueError(
                "An unsafe BPM %d >= 16777216 was passed. This BPM may not work on LR2.\
To allow, please set allow_unsafe in the BMSparser constructor.\
https://twitter.com/okunigon/status/1307656187832201217"
                % length
            )
        if length in self.bpm_objects:
            return self.bpm_objects[length]
        if self.bpm_index >= 1296:
            raise ValueError("Cannot use any more BPMs!")
        self.bpm_objects[length] = BMSparser.base_repr(self.bpm_index, 36).rjust(2, '0')
        self.bpm_index += 1
        return self.bpm_objects[length]

    @staticmethod
    def reindex_measure(measure, target):
        """
        Change a Measure object to reflect a new target size.
        Should probably be moved to the Measure class

        :param measure: Measure to reindex
        :type measure: Measure
        :param target: Target size
        :type target: int
        :return: New size
        :rtype: int
        """
        lcm = BMSparser.lcm(measure.size, target)
        if lcm != measure.size:
            for n in measure.notes:
                n.pos *= lcm // measure.size
            measure.size = lcm
        return lcm

    @staticmethod
    def _generic_add(target, f, lane, mes, length, pos, size, overwrite=False):
        """
        Add a note to a LL object in a targeted lane.
        The object number is determined by calling f(length).
        For use in stop_add/bpm_add.

        :param target: Target measure LL
        :type target: LL
        :param f: Function to call
        :type f: (int) -> str
        :param lane:
        :param mes:
        :param length:
        :param pos:
        :param size:
        :param overwrite:
        :return:
        """

        if size <= 0:
            raise ValueError("Invalid size")
        if mes in target:
            if target[mes].size != size:
                new = BMSparser.reindex_measure(target[mes], size)
                if new != size:
                    pos *= new // size
        else:
            target[mes] = Measure(size, lane, mes)
        idx = f(length)
        try:
            target[mes].add(Note(idx, pos, lane))
        except ValueError:
            if overwrite:
                for note in target[mes].notes:
                    if note.pos == pos:
                        target[mes].notes.remove(note)
                        break
                target[mes].add(Note(idx, pos, lane))
            else:
                print('Skipped', Note(idx, pos, lane))

    def stop_add(self, mes, length, pos, size, overwrite=False):
        """
        Add a stop the to BMS
        Example: stop_add(33, 192, 0, 1) adds a stop to measure 33 at position 0 of length 192

        :param mes: Measure number
        :type mes: int
        :param length: Stop length
        :type length: int
        :param pos: Position in measure
        :type pos: int
        :param size: Measure size
        :type size: int
        :param overwrite: Overwrite if exists in position
        :type overwrite: bool
        :return: None
        """
        BMSparser._generic_add(self.stop_measures, self._stop_index, Note.LANE_STOP, mes, length, pos, size, overwrite)

    def bpm_add(self, mes, bpm, pos, size, overwrite=False):
        """
        Add a BPM change the to BMS

        :param mes: Measure number
        :type mes: int
        :param bpm: Target BPM
        :type bpm: int
        :param pos: Position in measure
        :type pos: int
        :param size: Measure size
        :type size: int
        :param overwrite: Overwrite if exists in position
        :type overwrite: bool
        :return: None
        """
        BMSparser._generic_add(self.bpm_measures, self._bpm_index, Note.LANE_BPM, mes, bpm, pos, size, overwrite)

    def write_output(self, name, enc='cp932', skip_reverse_breakpoint=None, skip_reverse_delta=None):
        """
        Write out the BMS. Make sure to specify the same encoding it was read in.

        :param name: Filename to output to
        :type name: str
        :param enc: Encoding to use
        :type enc: str
        :param skip_reverse_breakpoint: If set, reverse by delta after this point
        :type skip_reverse_breakpoint: int | None
        :param skip_reverse_delta:
        :type skip_reverse_delta: int | None
        :return:
        """

        max_number = max(m.number for m in self.measures)
        max_number = max(max_number, self.meters.len-1, self.bpm_measures.len-1, self.stop_measures.len-1)
        if max_number >= 999:  # LR2 does not seem to like #999
            raise ValueError("Too many measures. No valid BMS can be produced %d" % max_number)

        print("<==============================>")
        print("Writing output to", name)
        print("Measure count:\t\t", str(max_number).rjust(4), '/ 999')
        f = open(name, 'w', encoding=enc)

        def delta(ii):
            if skip_reverse_breakpoint is not None:
                if ii >= skip_reverse_breakpoint:
                    return ii - skip_reverse_delta
            return ii

        for line in self.ignored_lines:
            f.write(line)
        for k, v in self.keysounds.items():
            f.write('#WAV%s %s\n' % (k, v))
        print("Stop object count:\t", str(self.stop_index).rjust(4), '/ 1296')
        for length, i in self.stop_objects.items():
            f.write('#STOP' + i + ' ' + str(length) + '\n')
        print("BPM object count:\t", str(self.bpm_index).rjust(4), '/ 1296')
        for bpm, i in self.bpm_objects.items():
            f.write('#BPM' + i + ' ' + str(bpm) + '\n')
        for mes, meter in self.meters.items():
            f.write('#' + '%03d' % delta(mes) + '02:' + str(meter) + '\n')
        print("Writing measures...")
        for index, mes in self.stop_measures.items():
            mes.number = delta(index)
            f.write(mes.get_string() + '\n')
        for index, mes in self.bpm_measures.items():
            mes.number = delta(index)
            f.write(mes.get_string() + '\n')
        for mes in self.measures:
            f.write(mes.get_string(delta(mes.number)) + '\n')

        print("Done!")
        print("<==============================>")

    def run(self, f, target_measures, target_lanes):
        """
        Run a function f on each measure in target_measures that match target_lanes.

        :param f: The function to run
        :type f: (Measure) -> Any
        :param target_measures: Measures to run it on
        :type target_measures: Iterable
        :param target_lanes: Lanes to match
        :type target_lanes: Iterable
        :return: None
        """
        for measure in self.find(target_measures, target_lanes):
            f(measure)

    def add(self, mes):
        """
        Add a measure to the BMS

        :param mes: Measure to add
        :type mes: Measure
        :return: None
        :rtype: None
        """
        self.measures.append(mes)

    def find(self, target_measures, target_lanes):
        """
        Locate a measure based on list of measure numbers and lanes.
        If target_measures/target_lanes is ['*'] then it will match everything.
        It is safe to remove as you iterate through the result.

        :param target_measures: Target measures
        :type target_measures: collections.Iterable[int] | collections.Iterable[str]
        :param target_lanes: Target lanes
        :type target_lanes: collections.Iterable[str]
        :return: List of matched measures
        :rtype: list[Measure]
        """
        res = []
        for measure in self.measures:
            if (measure.number in target_measures or target_measures == ['*']) and (
                    measure.lane in target_lanes or target_lanes == ['*']):
                res.append(measure)
        return res

    def shift_indices(self, start, delta=1):
        """
        Move all measures from start and above up by delta.

        :param start: Which measure to start at (inclusive!)
        :param delta: How many to move by
        :type start: int
        :type delta: int
        :return: None
        """
        for mes in self.measures:
            if mes.number >= start:
                mes.number += delta
        if start == 0:
            self.bpm_measures.shift_start(delta)
            self.stop_measures.shift_start(delta)
            self.meters.shift_start(delta)
            return
        for _ in range(delta):
            self.bpm_measures.append(start, None)
            self.stop_measures.append(start, None)
            self.meters.append(start, None)

    # TODO: not fully implemented start/end looping (or just rewrite this anyway)
    def add_mines(self, measure, f, *opt, target_lanes=Note.LANES_VISIBLE, mul=48, force_run=False):
        """
        Add mines to measures.
        Parameters: measure number, mines, target lanes, mine measure size.
        Mines can either be an array or a function that returns an array of mines.
        Mines should be in format [<int/str>lane, <int>position].
        If a function is passed, it will be called with a list of arrays in the measure matching the target lanes,
        the current note number in the lane, and any extra positional arguments passed to this function.
        Target lanes are the lanes for which mines will be added per object.

        :param measure: Measure to add the mines to
        :type measure: int
        :param f: Array of mines or function that takes measures and returns mines
        :type f: list | (Measure) -> collections.Iterable[list]
        :param opt: Options for function
        :param target_lanes: Target lanes to apply to
        :type target_lanes: collections.Iterable[str]
        :param mul: Measure size of mine measures
        :type mul: int
        :param force_run: Force function call even if no matching measures
        :type force_run: bool
        """
        start, end = measure
        cur_note = 0  # it will likely be first called with 1
        for i in range(start, end + 1):
            ml = {}
            targets = self.find([i], target_lanes)
            if len(targets) > 0:
                cur_note += 1  # assume only 1 real note per lane now
            elif not force_run or (i in self.meters and self.meters[i] < 1):
                continue
            ff = f(targets, cur_note, *opt) if callable(f) else f
            for j in ff:
                j[0] = 'D' + BMSparser.real_lane(j[0])
                if j[0] not in ml:
                    m = Measure(mul, j[0], i)
                    ml[j[0]] = m
                    self.add(m)
                ml[j[0]].add(Note(self.mine_damage, j[1], j[0]))

    def add_mines_stretched(self, mes, f, opt=None, target_lane=Note.LANES_VISIBLE, mul=32):
        """
        Add mines into a stretched single measure, old

        :param mes: Measure to add the mines to
        :type mes: int
        :param f: Array of mines or function that takes measures and returns mines
        :type f: list | (Measure) -> collections.Iterable[list]
        :param opt: Options for function
        :param target_lane: Target lanes to apply to
        :type target_lane: collections.Iterable[str]
        :param mul: Measure size of mine measures
        :type mul: int
        """
        note_pos = [n for m in self.find([mes], target_lane) for n in m.notes]
        note_pos.sort(key=lambda x: x.pos)
        cur_note = 0
        for i in range(0, int(self.meters[mes])):
            ml = {}
            first = False
            if cur_note < len(note_pos) - 1 and note_pos[cur_note + 1].pos <= i:
                first = True
                cur_note += 1
            ff = f(mes, cur_note, opt, first) if callable(f) else f
            for j in ff:
                j[0] = 'D' + BMSparser.real_lane(j[0])
                if j[0] not in ml:
                    m = Measure(self.meters[mes] * mul, j[0], mes)
                    ml[j[0]] = m
                    self.add(m)
                ml[j[0]].add(Note(self.mine_damage, i * mul + j[1], j[0]))

    def optimize(self):
        """
        Combine most extra BGA/BGM lanes that tend to be generated.
        It might be good to add more to this in the future.

        :rtype: None
        """

        # Query all bgm lanes and collapse
        print("<==============================>")
        print("Starting optimization pass...")

        removed = 0
        for lane in Note.LANES_BGA + (Note.LANE_BGM,):
            ms = self.find(['*'], [lane])
            ms.sort(key=lambda m: m.number)
            last_num = -1
            last_mes = None
            for i in range(len(ms)):
                if (last_mes is None) or (ms[i].number != last_num or last_mes.size != ms[i].size) \
                        or any(last_mes.contains_pos(m.pos) for m in ms[i].notes):
                    last_mes = Measure(ms[i].size, lane, ms[i].number)
                    last_num = ms[i].number
                    self.add(last_mes)
                else:
                    removed += 1

                for n in ms[i].notes:
                    last_mes.add(n)
                self.measures.remove(ms[i])
        print('Collapsed', removed, 'measures')
        # Remove empty measures
        removed = 0
        for mes in self.find(['*'], ['*']):
            if not mes.notes:
                removed += 1
                self.measures.remove(mes)
        print('Removed', removed, 'empty measures')
        # Set size of measures with only 1 object at t=0 to 1
        removed = 0
        all_measures = []
        for measure in self.stop_measures.values():
            all_measures.append(measure)
        for measure in self.bpm_measures.values():
            all_measures.append(measure)
        for measure in all_measures + self.measures:
            if measure.size > 1 and len(measure.notes) == 1 and measure.notes[0].pos == 0:
                measure.size = 1
                removed += 1
        print('Resized', removed, 'measures')
        print("Done!")
        print("<==============================>")

    @staticmethod
    def real_lane(lane):
        """
        Returns the second character of a real lane string of a lane number (0-7).

        :param lane: Lane number or string
        :type lane: str | int
        :rtype: str
        """
        if type(lane) == str:
            return lane[-1]  # Already a lane
        if lane == 0:
            return '6'
        if lane >= 6:
            lane += 2
        return str(lane)

    @staticmethod
    def lane_no(lane):
        """
        Returns the lane number (0-7) of a two-character lane string.

        :param lane: Lane number or string
        :type lane: str | int
        :rtype: int
        """
        if type(lane) == int:
            return lane
        if lane[-1] == '6':
            return 0
        if lane[-1] in ['8', '9']:
            return int(lane[-1]) - 2
        return int(lane[-1])

    @staticmethod
    def convert_pat_string(raw, mn=8, yes='X', offset=0, multiple=1):
        # noinspection SpellCheckingInspection
        """
        Convert a string containing a mine pattern into an array of mine notes as used by add_mines.
        mn is the number of mines
        i.e. convertPatString("XXXOOOO\nOOOXXXO\nOOOOOOX", 3)

        :param raw: Raw pattern string
        :type raw: str
        :param mn: Number of mines
        :type mn: int
        :param yes: "Yes" character
        :type yes: str
        :param offset: Offset (optional)
        :type offset: int
        :param multiple: Multiplicative factor (optional)
        :type offset: int
        :rtype: list
        """
        out = []
        for num, line in enumerate(raw.split('\n'), 1):
            for lane, letter in enumerate(line, 1):
                if letter == yes:
                    out.append([lane, multiple * (mn - num + offset)])
        return out


class InsertMesGimmick:
    """
    This class has methods to help with gimmicks where you want to make a new measure per target note.
    Helps keep track of offset measures.
    You should do the gimmicks in order of the original measures.
    """
    from collections import defaultdict

    def __init__(self, bms, max_bpm=0, norm_bpm=0, mes_div=32):
        """
        Max BPM should be something like XXX00XXX if the original is XXX.

        :param bms: The BMS object
        :type bms: BMSparser
        :param max_bpm: Max BPM
        :type max_bpm: int
        :param norm_bpm: Normal BPM
        :type norm_bpm: int
        :param mes_div: Measure size
        :type mes_div: int
        """
        self.insert_mes_offset = 0
        self.inserted_dict = {}
        self.max_bpm = max_bpm
        self.norm_bpm = norm_bpm
        self.mes_div = mes_div
        self.all_notes = self.defaultdict(list)
        self.bms = bms

    def add_max(self, measure):
        """
        Add a max BPM change at the original measure number.

        :param measure: Measure number
        :type measure: int
        :rtype: None
        """
        self.bms.bpm_add(measure + self.insert_mes_offset, self.max_bpm, 0, 1)

    # Add a normal bpm change at the original measure number.
    def add_norm(self, measure):
        """
        Add a normal BPM change at the original measure number.

        :param measure: Measure number
        :type measure: int
        :rtype: None
        """
        self.bms.bpm_add(measure + self.insert_mes_offset, self.norm_bpm, 0, 1)

    def run_adjusted(self, start, end, *a, **ka):
        """
        Run the make_dict function on the range from start to end.

        :param start: Start of range
        :param end: End of range
        :type start: int
        :type end: int
        :rtype: None
        """
        self.bms.run(self.make_dict, range(start + self.insert_mes_offset, end + self.insert_mes_offset), *a, **ka)

    def make_dict(self, measure):
        """
        Remove all real notes in specified measure and put them into a dictionary (all_notes)
        Recommended to use with run_adjusted

        :param measure: Measure to remove from
        :type measure: Measure
        :rtype: None
        """
        for n in measure.notes:
            self.all_notes[measure.number - self.insert_mes_offset].append(
                Note(n.object, (n.pos * self.mes_div) // measure.size, n.lane))
        self.bms.measures.remove(measure)

    def parse_dict(self, measure_range, target_lanes=Note.LANES_VISIBLE):
        """
        Create new measures on each target in measure_range, and make stops for each note.
        Use it after run_adjusted.
        Target lanes are lanes at which new measures should be created.
        With minimize lanes, measures that have no target notes will be collapsed.

        :param measure_range: collections.Iterable[int]
        :param target_lanes: collections.Iterable[str]
        :return: None
        """
        for measure_number in measure_range:
            # Determine the notes in the measure
            self.all_notes[measure_number].sort(
                key=lambda x: (x.pos, 0 if x.lane in target_lanes else int(x.lane)))  # Place targets at beginning
            start_measure = measure_number + self.insert_mes_offset  # This is the real starting measure
            print("Starting ", measure_number, " at ", start_measure)
            # Try to group notes that are at the same time together
            cur_note_index = 0
            note_collection = []
            previous_hit_time = 0
            previous_note_time = 0
            time_unchanged = True
            print("All notes in measure")
            print(self.all_notes[measure_number])
            while cur_note_index < len(self.all_notes[measure_number]):
                cur_note = self.all_notes[measure_number][cur_note_index]
                print("Current note", cur_note)
                if cur_note.pos == previous_hit_time:
                    # Add the note to the collection with a corrected time of 0
                    note_collection.append(Note(cur_note.object, 0, cur_note.lane))
                else:
                    if cur_note.lane in target_lanes:
                        # Edge case: first target note on 0, we don't want to make a new measure
                        if cur_note.pos != 0:
                            # Empty note collection into measure, make a new one
                            # We pass the distance from the previous note to the end of the measure also
                            self.__parse_dict_make_measure(measure_number, note_collection,
                                                           cur_note.pos - previous_note_time, not time_unchanged)
                            # Reset notes and update time
                            note_collection.clear()
                            previous_hit_time = cur_note.pos
                        note_collection.append(Note(cur_note.object, 0, cur_note.lane))
                        time_unchanged = True
                    elif time_unchanged:
                        # Very similar to above but collapse
                        self.__parse_dict_make_measure(measure_number, note_collection,
                                                       cur_note.pos - previous_note_time, not time_unchanged)
                        note_collection.clear()
                        previous_hit_time = cur_note.pos
                        note_collection.append(Note(cur_note.object, 0, cur_note.lane))
                        time_unchanged = False
                    else:
                        # Add the note to collection with a corrected time based on distance from previous (in mes_div)
                        note_collection.append(Note(cur_note.object, cur_note.pos - previous_hit_time, cur_note.lane))
                previous_note_time = cur_note.pos
                cur_note_index += 1
            # Now clean off the remaining ones
            self.__parse_dict_make_measure(measure_number, note_collection, self.mes_div - previous_note_time, False)
            # Record where measures got expanded
            self.inserted_dict[measure_number] = [start_measure, measure_number + self.insert_mes_offset]

    # TODO
    # Why are extra measures generated at the end of each measure? Not a big deal now at least..

    def __parse_dict_make_measure(self, measure_number, note_collection, pad_distance, collapse):
        """
        Helper function for above that creates a measure at the number and inserts notes/stops from a dictionary.
        """
        print("Note collection", note_collection)
        assert (len(note_collection) != 0)
        self.bms.shift_indices(measure_number + self.insert_mes_offset + 1)
        new_measures = {}
        prev_time = 0
        for note in note_collection:
            # Create a measure if needed for the lane
            # For BGM lanes, we want duplicates
            if note.lane not in new_measures or note.lane == '01':
                new_measure = Measure(self.mes_div, note.lane, measure_number + self.insert_mes_offset)
                self.bms.add(new_measure)
                new_measures[note.lane] = new_measure
            # Add the stop for the note if the time is different at the previous one
            if note.pos != prev_time:
                self.bms.stop_add(measure_number + self.insert_mes_offset,
                                  ((note.pos - prev_time) / self.mes_div) * (192 * self.max_bpm / self.norm_bpm),
                                  prev_time, self.mes_div)
                prev_time = note.pos
            new_measures[note.lane].add(note)
        # Add the stop for the padding distance
        self.bms.stop_add(measure_number + self.insert_mes_offset,
                          (pad_distance / self.mes_div) * (192 * self.max_bpm / self.norm_bpm), prev_time, self.mes_div)
        print("Made measure at ", measure_number + self.insert_mes_offset)
        if collapse:
            self.bms.meters[measure_number + self.insert_mes_offset] = 1 / 1920
            print("Minimizing", measure_number + self.insert_mes_offset)
        self.insert_mes_offset += 1

    def parse_dict_old(self, r, pos_factor=0, no_move_target=False, make_on_end=False, target_lanes=Note.LANES_VISIBLE,
                       minimize_lanes=True, check_dist_advance=False, move_all=False):
        """
        Old version of parse_dict, not recommended and buggy

        :type r: list
        :type pos_factor: float | (int, Note) -> float
        :type no_move_target: bool
        :type make_on_end: bool
        :type target_lanes: collections.Iterable[str]
        :type minimize_lanes: bool
        :type check_dist_advance: bool
        :type move_all: bool
        """
        stop_loc = 0
        np = None
        for k in r:
            self.all_notes[k].sort(key=lambda x: (x.pos, -int(x.lane)))  # Push notes to front
            start = k + self.insert_mes_offset
            # We need to iterate through first to identify where we can start/end single measures.
            # Ideally everything besides visible notes can be shoved into an 1/1920 measure
            target_indices = [i for i in range(len(self.all_notes[k])) if self.all_notes[k][i].lane in target_lanes]
            for i in range(len(self.all_notes[k])):
                new_note = Note(self.all_notes[k][i].object, self.all_notes[k][i].pos, self.all_notes[k][i].lane)
                if check_dist_advance:
                    np = self.all_notes[k][i + 1].pos if i != len(self.all_notes[k]) - 1 else self.mes_div
                if not no_move_target:
                    if i in target_indices:  # Push up once
                        if not check_dist_advance or (np - new_note.pos != 0):
                            if i - 1 not in target_indices and minimize_lanes:
                                self.bms.meters[k + self.insert_mes_offset] = 1 / 1920  # Bgm only measures
                            self.insert_mes_offset += 1
                            self.bms.shift_indices(k + self.insert_mes_offset)
                        if callable(pos_factor):
                            pos_factor(k, new_note)  # can also change other properties of note, will be used
                        else:
                            new_note.pos = int(new_note.pos * pos_factor)
                        stop_loc = 0
                    else:
                        if i - 1 in target_indices and minimize_lanes:
                            self.bms.meters[k + self.insert_mes_offset] = 1
                            self.insert_mes_offset += 1
                            self.bms.shift_indices(k + self.insert_mes_offset)
                        if callable(pos_factor) and move_all:
                            pos_factor(k, new_note)
                        stop_loc = new_note.pos
                np = self.all_notes[k][i + 1].pos if i != len(self.all_notes[k]) - 1 else self.mes_div
                m = Measure(self.mes_div, new_note.lane, k + self.insert_mes_offset)
                m.add(new_note)
                self.bms.add(m)
                if (np - self.all_notes[k][i].pos) != 0:
                    self.bms.stop_add(k + self.insert_mes_offset, ((np - self.all_notes[k][i].pos) / self.mes_div) * (
                            192 * self.max_bpm / self.norm_bpm), stop_loc, self.mes_div)
            if minimize_lanes:
                self.bms.meters[k + self.insert_mes_offset] = 1 / 1920  # last one too!
            if make_on_end:
                self.insert_mes_offset += 1
                self.bms.shift_indices(k + self.insert_mes_offset)
                self.bms.add(Measure(1, '01', k + self.insert_mes_offset))
            self.inserted_dict[k] = [start, k + self.insert_mes_offset]


# This class contains tools for animations from images
class AnimationGimmick:
    import skimage.transform as transform

    def __init__(self, img):
        assert(type(img) == InsertMesGimmick)
        self.g = img

    # We are forced to a width of 8
    def frame_to_mine_array(self, frame, height=64, threshold=0.5):
        frame = self.transform.resize(frame, (height, 8), order=1)

        mines = []
        # Make a mine if any position is over the threshold
        for x in range(8):
            for y in range(height):
                if any(channel > threshold for channel in frame[y][x]):
                    mines.append([x, y])

        return mines


def randomize(bms, start, end, div, upper_limit=7, keys=(1, 2, 3, 4, 5, 6, 7)):
    """
    Create a randomizer pulling elements from the BGM lanes in measure range [start, end).
    :param bms: BMSparser
    :param start: int
    :param end: int
    :param div: int
    :param upper_limit: int
    :param keys: Iterable
    :return: None
    """

    from collections import defaultdict
    from itertools import combinations

    for measure_number in range(start, end):
        usable = defaultdict(list)
        for measure in bms.find([measure_number], [Note.LANE_BGM]):
            # Pull up to 6
            del_queue = []
            msx = measure.size
            if measure_number in bms.meters:
                msx /= bms.meters[measure_number]
            if div % msx == 0:
                for note in measure.notes:
                    if len(usable[note.pos * (div // msx)]) < upper_limit:
                        usable[note.pos * (div // msx)].append(note.object)
                        del_queue.append(note)  # 4.13
            for note in del_queue:
                measure.notes.remove(note)
        for pos, objects in usable.items():
            possibilities = list(combinations(keys, 7 - len(objects)))
            bms.ignored_lines.append('#RANDOM ' + str(len(possibilities)) + '\n')
            if pos != 0:
                new_pos = pos
                new_div = div
                if measure_number in bms.meters:
                    new_div *= bms.meters[measure_number]
                while new_pos / 2 % 1 == 0 and new_div / 2 % 1 == 0:
                    new_pos /= 2
                    new_div /= 2
            else:
                new_pos = 0
                new_div = 1
            for n, possibility in enumerate(possibilities, 1):
                bms.ignored_lines.append('#IF ' + str(n) + '\n')
                object_num = 0
                for key in keys:
                    if key not in possibility:
                        temp = Measure(new_div, '1' + BMSparser.real_lane(key), measure_number)
                        temp.add(Note(objects[object_num], int(new_pos)))
                        bms.ignored_lines.append(temp.get_string() + '\n')
                        object_num += 1
                bms.ignored_lines.append('#ENDIF' + '\n')
