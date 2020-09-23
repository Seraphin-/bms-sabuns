# API Ver: 1.1

# Classes to abstract away BMS for making gimmick charts...
# o = BMSparser('input.bme')
# (do stuff)
# o.write_output('output.bme')
# Produces big BMS files very slowly. Loading into uBMSC and resaving fixes a lot of that.

# Make sure to parse measures in order if you are inserting new ones...

# Use a LL data structure to provide easily re-indexable insertion/deletion.
# Uses numerical keys only.
# We use this instead of dicts for single mes:value pairs.
class LLNode:
	def __init__(self, v, next=None):
		self.value = v
		self.next = next

	def __repr__(self):
		return "LLNode(" + repr(self.value) + ")"

class LLError(Exception):
	pass

# Imagine actually using a linked list for anything
class LL:
	def __init__(self):
		self.len = 0
		self.start = None
		self.end = None

	def _traverse(self, index):
		if self.start == None: raise LLError('Empty LL')
		cur = self.start
		for i in range(index):
			cur = cur.next
		return cur

	def __getitem__(self, index):
		if index < 0: raise LLError('Negative index')
		if index > self.len: raise LLError('Attempted to access index past end')
		n = self._traverse(index)
		if n.value == None: raise LLError('Empty node')
		return n.value

	def __setitem__(self, index, value):
		if index < 0: raise LLError('Negative index')
		if index >= self.len:
			if self.len == 0:
				bn = LLNode(None)
				self.len = 1
				self.start = bn
			else: bn = self.end
			for i in range(index-self.len+1):
				bn.next = LLNode(None)
				bn = bn.next
			self.len = index+1
			self.end = bn
		else: bn = self._traverse(index)
		bn.value = value

	def __contains__(self, item):
		return item < self.len and item >= 0 and (self._traverse(item).value is not None)

	def append(self, index, value):
		if self.len == 0 or index >= self.len: self[index] = value #just shove it in
		n = self._traverse(index-1)
		nn = n.next
		n.next = LLNode(value)
		self.len += 1
		n.next.next = nn

	def items(self):
		if self.len == 0: return []
		def ll_iter_items():
			cur = self.start
			i = 0
			if self.start.value is not None: yield (i, self.start.value)
			while cur.next is not None:
				cur = cur.next
				i += 1
				if cur.value is not None: yield (i, cur.value)
			raise StopIteration()
		return ll_iter_items()

	def values(self):
		if self.len == 0: return []
		def ll_iter_values():
			cur = self.start
			if self.start.value is not None: yield self.start.value
			while cur.next is not None:
				cur = cur.next
				if cur.value is not None: yield cur.value
			raise StopIteration()
		return ll_iter_values()		

class Note:
	LANE_BGM = '01'
	LANE_BPM = '08'
	LANE_STOP = '09'
	LANES_BGA = ['04', '06', '07', '0A']
	LANES_VISIBLE = ['11', '12', '13', '14', '15', '16', '18', '19']
	LANES_LN = ['51', '52', '53', '54', '55', '56', '58', '59']

	@staticmethod
	def clone(new):
		return Note(new.object, new.pos, new.lane, new.size)

	def __init__(self, sound, position, lane=None, size=None): # Lane and size here do NOT reflect in output
		self.object = sound
		self.pos = position
		self.lane = lane
		self.size = size

	def __repr__(self):
		return "Note(%s, %s, %s)" % (self.object, self.pos, self.lane) 

class Measure:
	DP_MINE = False
	def __init__(self, size, lane, number, meter=None): # Meter does NOT reflect in output, use BMSparser.meters
		if(size % 1 != 0): raise ValueError("Invalid size %s" % size)
		self.base_meter = meter
		self.meter = meter # Autoconvert when changed from base?
		self.number = number
		self.size = int(size)
		self.lane = lane if (lane[0] != 'D' or not self.DP_MINE) else ('E' + lane[1])
		self.notes = []

	def get_string(self):
		basestr = '#' + '%03d' % self.number + self.lane + ':'
		notes = ['00'] * self.size
		try:
			for n in self.notes:
				notes[n.pos] = n.object
		except IndexError:
			print('---- ERROR ----', self)
			raise IndexError
		return basestr + ''.join(notes)

	def add(self, note):
		if not all(n.pos != note.pos for n in self.notes): raise ValueError('Duplicate note position in single measure not currently supported')
		self.notes.append(note)

	def contains_pos(self, i):
		return any(m.pos == i for m in self.notes)

	def __repr__(self):
		return "Measure(%s, %s, %s, %s), Notes [\n\t" % (self.size, self.lane, self.number, self.meter) + "\n\t".join(repr(n) for n in self.notes) + "\n]"

class BMSparser:
	from numpy import lcm
	VERSION = '1.1'

	def __init__(self, name, enc='utf-8'):
		self.measures = []
		self.stop_objects = {} # key/value length/index
		self.stop_index = 1
		self.stop_measures = LL() # key/value mes/measure
		self.bpm_objects = {} # key/value bpm/index
		self.bpm_index = 10 # bug with ubmsc might require starting at 10...?
		self.bpm_measures = LL() # key/value mes/measure
		self.meters = LL() # key/value measure/meter
		self.ignored_lines = []
		self.mine_damage = '01'
		# Dict of list of Measure objects per measure. Allowing multiple lets us split up polyrhythms without making excessively long lines.
		# For now we just make a new measure object per line since it's easy.
		# We can also split up STOP lines and so on the same way.
		self._parse(name, enc)

	def _parse(self, name, enc):
		for line in open(name, 'r', encoding=enc):
			if line[0] == '#' and line[1].isnumeric():
				mi = int(line[1:4])
				if line[4:6] == '02':
					self.meters[mi] = float(line[7:])
					continue
				m = Measure((len(line)-8)/2, line[4:6], mi, self.meters[mi] if mi in self.meters else 1)
				[m.add(Note(line[7+i*2:9+i*2], i, line[4:6], (len(line)-8)/2)) for i in range((len(line)-8)//2) if line[7+i*2:9+i*2] != '00']
				self.measures.append(m)
			elif line != '\n':
				self.ignored_lines.append(line)

	def _stop_index(self, length):
		if length in self.stop_objects: return self.stop_objects[length]
		self.stop_objects[length] = '%02X' % self.stop_index
		self.stop_index += 1
		return self.stop_objects[length]

	def _bpm_index(self, length):
		if length in self.bpm_objects: return self.bpm_objects[length]
		self.bpm_objects[length] = '%02X' % self.bpm_index
		self.bpm_index += 1
		return self.bpm_objects[length]

	def _reindex_measure(self, measure, target):
		lcm = self.lcm(measure.size, target)
		if lcm != measure.size:
			for n in measure.notes:
				n.pos *= lcm // measure.size
			measure.size = lcm
		return lcm

	def _generic_add(self, target, f, lane, mes, length, pos, size):
		if mes in target:
			if target[mes].size != size:
				new = self._reindex_measure(target[mes], size)
				if new != size: pos *= new // size
		else: target[mes] = Measure(size, lane, mes)
		idx = f(length)
		try:
			target[mes].add(Note(idx, pos, lane))
		except ValueError:
			print('Skipped', Note(idx, pos, lane))

	# stop_add/bpm_add arguments
	# measure to add stop to, length of stop/bpm, position in measure (int), measure division size

	def stop_add(self, *a):
		self._generic_add(self.stop_measures, self._stop_index, Note.LANE_STOP, *a)

	def bpm_add(self, *a):
		self._generic_add(self.bpm_measures, self._bpm_index, Note.LANE_BPM, *a)

	def write_output(self, name, enc='utf-8'):
		f = open(name, 'w', encoding=enc);
		for line in self.ignored_lines: f.write(line)
		for length, i in self.stop_objects.items(): f.write('#STOP' + i + ':' + str(length) + '\n')
		for bpm, i in self.bpm_objects.items(): f.write('#BPM' + i + ':' + str(bpm) + '\n')
		for mes, meter in self.meters.items(): f.write('#' + '%03d' % mes + '02:' + str(meter) + '\n')
		for index, mes in self.stop_measures.items():
			mes.number = index
			f.write(mes.get_string() + '\n')
		for index, mes in self.bpm_measures.items():
			mes.number = index
			f.write(mes.get_string() + '\n')
		for mes in self.measures: f.write(mes.get_string() + '\n')

	def run(self, f, target_measures, target_lanes):
		for measure in self.find(target_measures, target_lanes):
			f(measure)

	def add(self, mes):
		self.measures.append(mes)

	def find(self, target_measures, target_lanes):
		# If target_measures/target_lanes is ['*'] then it will match everything
		res = []
		for measure in self.measures:
			if (measure.number in target_measures or target_measures == ['*']) and (measure.lane in target_lanes or target_lanes == ['*']):
				res.append(measure)
		return res

	def shift_indices(self, start, delta=1): # Shift up measure numbers
		for mes in self.measures:
			if mes.number >= start: mes.number += delta
		for _ in range(delta):
			self.bpm_measures.append(start, None)
			self.stop_measures.append(start, None)
			self.meters.append(start, None)

	def add_mines(self, mes, f, *opt, target_lanes=Note.LANES_VISIBLE, mul=48, force_run=False):
		# Target lanes initiate a state change
		# f can be an array of mine objects or callable (additional arg to callable can be passed as opt)
		# mines should be in format [<int/str>lane, <int>delta]
		start, end = mes
		curnote = 0 # it will likely be first called with 1
		for i in range(start, end+1):
			ml = {}
			targets = self.find([i], target_lanes)
			if len(targets) > 0:
				curnote += 1 # assume only 1 real note per lane now
			elif not force_run or (i in self.meters and self.meters[i] < 1): continue
			ff = f(targets, curnote, *opt) if callable(f) else f
			for j in ff:
				j[0] = 'D' + BMSparser._real_lane(j[0])
				if j[0] not in ml:
					m = Measure(mul, j[0], i)
					ml[j[0]] = m
					self.add(m)
				ml[j[0]].add(Note(self.mine_damage, j[1], j[0]))

	def add_mines_stretched(self, mes, f, opt=None, target_lane=Note.LANES_VISIBLE, mul=32):
		# Target lanes initiate a state change
		# f can be an array of mine objects or callable (additional arg to callable can be passed as opt)
		# mines should be in format [<str>lane, <int>delta]
		note_pos = [n for m in self.find([mes], target_lane) for n in m.notes]
		note_pos.sort(key=lambda x: x.pos)
		curnote = 0
		for i in range(0, int(self.meters[mes])):
			ml = {}
			first = False
			if curnote < len(note_pos)-1 and note_pos[curnote+1].pos <= i:
				first = True
				curnote += 1
			ff = f(mes, curnote, opt, first) if callable(f) else f
			for j in ff:
				j[0] = 'D' + BMSparser._real_lane(j[0])
				if j[0] not in ml:
					m = Measure(self.meters[mes]*mul, j[0], mes)
					ml[j[0]] = m
					self.add(m)
				ml[j[0]].add(Note(self.mine_damage, i*mul+j[1], j[0]))

	def optimize(self):
		# Query all bgm lanes and collapse
		removed = 0
		for lane in Note.LANES_BGA + [Note.LANE_BGM]:
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
				else: removed += 1
				for n in ms[i].notes: last_mes.add(n)
				self.measures.remove(ms[i])
		print('collapsed', removed, 'measures')

	@staticmethod
	def _real_lane(lane):
		if type(lane) == str: return lane[1] # Already a lane
		if lane == 0: return '6'
		if lane >= 6: lane += 2
		return str(lane)

	@staticmethod
	def _lane_no(lane):
		if type(lane) == int: return lane
		if lane[1] == '6': return 0
		if lane[1] in ['8', '9']: return int(lane[1]) - 2
		return int(lane[1])

	# i.e. convertPatString("XXXOOOO\nOOOXXXO\nOOOOOOX", 3)
	@staticmethod
	def convert_pat_string(raw, mn=8, yes='X', offset=0):
		out = []
		for num, line in enumerate(raw.split('\n'), 1):
			for lane, letter in enumerate(line, 1):
				if letter == yes: out.append([lane, mn-num+offset])
		return out

class InsertMesGimmick: #help with making gimmicks where you want to insert a new measure per target
	from collections import defaultdict

	def __init__(self, bms, maxbpm, normbpm, mes_div):
		self.insert_mes_offset = 0
		self.inserted_dict = {}
		self.maxbpm = maxbpm
		self.normbpm = normbpm
		self.mes_div = mes_div
		self.all_notes = self.defaultdict(list)
		self.bms = bms

	def add_max(self, measure):
		self.bms.bpm_add(measure+self.insert_mes_offset, self.maxbpm, 0, 1)

	def add_norm(self, measure):
		self.bms.bpm_add(measure+self.insert_mes_offset, self.normbpm, 0, 1)

	def run_adjusted(self, start, end, *a, **ka):
		self.bms.run(self.make_dict, range(start+self.insert_mes_offset, end+self.insert_mes_offset), *a, **ka)

	def make_dict(self, measure):
		for n in measure.notes:
			self.all_notes[measure.number-self.insert_mes_offset].append(Note(n.object, (n.pos*self.mes_div)//measure.size, n.lane))
		self.bms.measures.remove(measure)

	def parse_dict(self, r, pos_factor=0, nomove_target=False, make_on_end=False, target_lanes=Note.LANES_VISIBLE, minimize_lanes=True, check_dist_advance=False, move_all=False):
		for k in r:
			self.all_notes[k].sort(key=lambda x: (x.pos, -int(x.lane))) # Push notes to front
			start = k+self.insert_mes_offset
			# We need to iterate through first to identify where we can start/end single measures. Ideally everything besides visible notes can be shoved into an 1/1920 measure
			target_indices = [i for i in range(len(self.all_notes[k])) if self.all_notes[k][i].lane in target_lanes]
			for i in range(len(self.all_notes[k])):
				newnote = Note(self.all_notes[k][i].object, self.all_notes[k][i].pos, self.all_notes[k][i].lane)
				if check_dist_advance:
					np = self.all_notes[k][i+1].pos if i != len(self.all_notes[k])-1 else self.mes_div
				if not nomove_target:
					if i in target_indices: # Push up once
						if not check_dist_advance or (np - newnote.pos != 0):
							if i-1 not in target_indices and minimize_lanes: self.bms.meters[k+self.insert_mes_offset] = 1/1920 #Bgm only measures
							self.insert_mes_offset += 1
							self.bms.shift_indices(k+self.insert_mes_offset)
						if callable(pos_factor):
							pos_factor(k, newnote) # can also change other properties of note, will be used
						else: newnote.pos = int(newnote.pos*pos_factor)
						stop_loc = 0
					else:
						if i-1 in target_indices and minimize_lanes:
							self.bms.meters[k+self.insert_mes_offset] = 1
							self.insert_mes_offset += 1
							self.bms.shift_indices(k+self.insert_mes_offset)
						if callable(pos_factor) and move_all:
							pos_factor(k, newnote)
						stop_loc = newnote.pos
				np = self.all_notes[k][i+1].pos if i != len(self.all_notes[k])-1 else self.mes_div
				m = Measure(self.mes_div, newnote.lane, k+self.insert_mes_offset)
				m.add(newnote)
				self.bms.add(m)
				if (np - self.all_notes[k][i].pos) != 0:
					self.bms.stop_add(k+self.insert_mes_offset, ((np - self.all_notes[k][i].pos) / self.mes_div) * (192 * self.maxbpm / self.normbpm), stop_loc, self.mes_div)
			if minimize_lanes: self.bms.meters[k+self.insert_mes_offset] = 1/1920 # last one too!
			if make_on_end:
				self.insert_mes_offset += 1
				self.bms.shift_indices(k+self.insert_mes_offset)
				self.bms.add(Measure(1, '01', k+self.insert_mes_offset))
			self.inserted_dict[k] = [start, k+self.insert_mes_offset]