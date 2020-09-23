# API Ver: 1.3

# Classes to abstract away BMS for making gimmick charts...
# o = BMSparser('input.bme')
# (do stuff)
# o.optimize()
# o.write_output('output.bme')
# Produces big BMS files very slowly.

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

# Represents a single note
# Also contains static attributes with common lane numbers
class Note:
	LANE_BGM = '01'
	LANE_BPM = '08'
	LANE_STOP = '09'
	LANES_BGA = ['04', '06', '07', '0A']
	LANES_VISIBLE = ['11', '12', '13', '14', '15', '16', '18', '19']
	LANES_LN = ['51', '52', '53', '54', '55', '56', '58', '59']

	# Get a copy of a note object
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

# Represents a measure of one lane.
# Note that one lane/measure combo can have multiple Measure objects corresponding to it.
# They will be combined if possible like standard BMS,
# but an error will be thrown if you have two objects at the same position in non-BGM lanes.
class Measure:
	DP_MINE = False # Set this to true to force all mines to be moved to the DP side.
	def __init__(self, size, lane, number, meter=None): # Meter does NOT reflect in output, use BMSparser.meters
		# The size of a measure should be a whole number, and if it's not an integer it will be converted here.
		if(size % 1 != 0): raise ValueError("Invalid size %s" % size)
		self.base_meter = meter
		self.meter = meter # Possible feature: autoconvert when changed from base?
		self.number = number
		self.size = int(size)
		self.lane = lane if (lane[0] != 'D' or not self.DP_MINE) else ('E' + lane[1])
		self.notes = []

	# Retuns a valid BMS line representation of the measure
	def get_string(self, mes=None):
		if mes == None: mes = self.number
		basestr = '#' + '%03d' % mes + self.lane + ':'
		notes = ['00'] * self.size
		try:
			for n in self.notes:
				notes[n.pos] = n.object
		except IndexError:
			print('---- ERROR ----', self)
			raise IndexError
		return basestr + ''.join(notes)

	# Add a note to the measure. Validates that all notes are in unique positions.
	# If you want multiple BGM notes at the same place, make another Measure object.
	# The BMSparser.optimize method will get rid of most excess measure lines.
	def add(self, note):
		if not all(n.pos != note.pos for n in self.notes): raise ValueError('Duplicate note position in single measure not currently supported')
		self.notes.append(note)

	# Returns true if there is a note with position i in the measure.
	def contains_pos(self, i):
		return any(m.pos == i for m in self.notes)

	def __repr__(self):
		return "Measure(%s, %s, %s, %s), Notes [\n\t" % (self.size, self.lane, self.number, self.meter) + "\n\t".join(repr(n) for n in self.notes) + "\n]"

# Class to parse BMS files.
class BMSparser:
	from numpy import lcm
	VERSION = '1.3'

	# The default encoding is SJIS.
	def __init__(self, name, enc='cp932'):
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
		self.__parse(name, enc)

	# This should not need to be called explicitly.
	def __parse(self, name, enc):
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

	# Returns the number to use of the stop object corresponding to the stop length.
	def _stop_index(self, length):
		if length in self.stop_objects: return self.stop_objects[length]
		self.stop_objects[length] = '%02X' % self.stop_index
		self.stop_index += 1
		return self.stop_objects[length]

	# See above, but for BPM.
	def _bpm_index(self, length):
		if length in self.bpm_objects: return self.bpm_objects[length]
		self.bpm_objects[length] = '%02X' % self.bpm_index
		self.bpm_index += 1
		return self.bpm_objects[length]

	# Change a Measure object to reflect a new target size.
	# Should probably be moved to the Measure class...
	def _reindex_measure(self, measure, target):
		lcm = self.lcm(measure.size, target)
		if lcm != measure.size:
			for n in measure.notes:
				n.pos *= lcm // measure.size
			measure.size = lcm
		return lcm

	# Add a note to a LL object in a targerted lane.
	# The object number is determined by calling f(length).
	# For use in stop_add/bpm_add.
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

	# Add a stop to the BMS.
	# Arguments: Target measure number, length of stop, position in measure (integer), and the measure division size.
	# Example: stop_add(33, 192, 0, 1) adds a stop to measure 33 at position 0 of length 192
	def stop_add(self, *a):
		self._generic_add(self.stop_measures, self._stop_index, Note.LANE_STOP, *a)

	# Same as above, but for BPM changes.
	def bpm_add(self, *a):
		self._generic_add(self.bpm_measures, self._bpm_index, Note.LANE_BPM, *a)

	# Write out the BMS. Make sure to specify the same encoding it was read in.
	def write_output(self, name, enc='cp932', skip_reverse_breakpoint=None, skip_reverse_delta=None):
		f = open(name, 'w', encoding=enc)
		def delta(i):
			if skip_reverse_breakpoint is not None:
				if i >= skip_reverse_breakpoint: return i - skip_reverse_delta
			return i
		for line in self.ignored_lines: f.write(line)
		for length, i in self.stop_objects.items(): f.write('#STOP' + i + ':' + str(length) + '\n')
		for bpm, i in self.bpm_objects.items(): f.write('#BPM' + i + ':' + str(bpm) + '\n')
		for mes, meter in self.meters.items(): f.write('#' + '%03d' % delta(mes) + '02:' + str(meter) + '\n')
		for index, mes in self.stop_measures.items():
			mes.number = delta(index)
			f.write(mes.get_string() + '\n')
		for index, mes in self.bpm_measures.items():
			mes.number = delta(index)
			f.write(mes.get_string() + '\n')
		for mes in self.measures: f.write(mes.get_string(delta(mes.number)) + '\n')

	# Run a function f on each measure in target_measures that match target_lanes.
	def run(self, f, target_measures, target_lanes):
		for measure in self.find(target_measures, target_lanes):
			f(measure)

	# Add a measure to the BMS.
	def add(self, mes):
		self.measures.append(mes)

	# Locate a measure based on list of measure numbers and lanes.
	# If target_measures/target_lanes is ['*'] then it will match everything.
	def find(self, target_measures, target_lanes):
		res = []
		for measure in self.measures:
			if (measure.number in target_measures or target_measures == ['*']) and (measure.lane in target_lanes or target_lanes == ['*']):
				res.append(measure)
		return res

	# Move all measures from start and above up by delta.
	def shift_indices(self, start, delta=1): # Shift up measure numbers
		for mes in self.measures:
			if mes.number >= start: mes.number += delta
		for _ in range(delta):
			self.bpm_measures.append(start, None)
			self.stop_measures.append(start, None)
			self.meters.append(start, None)

	# Add mines	to measures.
	# Parameters: measure number, mines, target lanes, mine measure size.
	# Mines can either be an array or a function that returns an array of mines.
	# Mines should be in format [<int/str>lane, <int>position].
	# If a function is passed, it will be called with a list of arrays in the measure matching the target lanes,
	#    the current note number in the lane, and any extra positional arguments passed to this function.
	# Target lanes are the lanes for which mines will be added per object.
	# TODO: not fully implemented start/end looping (or just rewrite this anyway)
	def add_mines(self, measure, f, *opt, target_lanes=Note.LANES_VISIBLE, mul=48, force_run=False):
		start, end = measure
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

	# Add mines into a streched single measure, old
	def add_mines_stretched(self, mes, f, opt=None, target_lane=Note.LANES_VISIBLE, mul=32):
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

	# Combine most extra BGA/BGM lanes that tend to be generated.
	# It might be good to add more to this in the future.
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
		# Remove empty measures
		removed = 0
		for mes in self.find(['*'], ['*']):
			if not mes.notes:
				removed += 1
				self.measures.remove(mes)
		print('removed', removed, 'empty measures')
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
		print('resized', removed, 'measures')

	# Returns the second character of a real lane string of a lane number (0-7).
	@staticmethod
	def _real_lane(lane):
		if type(lane) == str: return lane[1] # Already a lane
		if lane == 0: return '6'
		if lane >= 6: lane += 2
		return str(lane)

	# Returns the lane number (0-7) of a two-character lane string.
	@staticmethod
	def _lane_no(lane):
		if type(lane) == int: return lane
		if lane[1] == '6': return 0
		if lane[1] in ['8', '9']: return int(lane[1]) - 2
		return int(lane[1])

	# Convert a string containing a mine pattern into an array of mine notes as used by add_mines.
	# mn is the number of mines
	# i.e. convertPatString("XXXOOOO\nOOOXXXO\nOOOOOOX", 3)
	@staticmethod
	def convert_pat_string(raw, mn=8, yes='X', offset=0, multiple=1):
		out = []
		for num, line in enumerate(raw.split('\n'), 1):
			for lane, letter in enumerate(line, 1):
				if letter == yes: out.append([lane, multiple*(mn-num+offset)])
		return out

# This class has methods to help with gimmicks where you want to make a new measure per target note.
# Helps keep track of offset measures.
# You should do the gimmicks in order of the original measures.
class InsertMesGimmick:
	from collections import defaultdict

	# MAXBPM should be something like XXX000XXX if the original is XXX.
	def __init__(self, bms, maxbpm, normbpm, mes_div):
		self.insert_mes_offset = 0
		self.inserted_dict = {}
		self.maxbpm = maxbpm
		self.normbpm = normbpm
		self.mes_div = mes_div
		self.all_notes = self.defaultdict(list)
		self.bms = bms

	# Add a maxbpm change at the original measure number.
	def add_max(self, measure):
		self.bms.bpm_add(measure+self.insert_mes_offset, self.maxbpm, 0, 1)

	# Add a normal bpm change at the original measure number.
	def add_norm(self, measure):
		self.bms.bpm_add(measure+self.insert_mes_offset, self.normbpm, 0, 1)

	# Run the make_dict function on the range from start to end.
	def run_adjusted(self, start, end, *a, **ka):
		self.bms.run(self.make_dict, range(start+self.insert_mes_offset, end+self.insert_mes_offset), *a, **ka)

	# Remove all real notes in specified measure and put them into a dictionary (all_notes)
	# Reccomened to use with run_adjusted
	def make_dict(self, measure):
		for n in measure.notes:
			self.all_notes[measure.number-self.insert_mes_offset].append(Note(n.object, (n.pos*self.mes_div)//measure.size, n.lane))
		self.bms.measures.remove(measure)

	# Create new measures on each target in measure_range, and make stops for each note.
	# Use it after run_adjusted.
	# Target lanes are lanes at which new measures should be created.
	# With minimize lanes, measures that have no target notes will be collapsed.
	def parse_dict(self, measure_range, target_lanes=Note.LANES_VISIBLE, minimize_lanes=True):
		for measure_number in measure_range:
			# Determine the notes in the measure
			self.all_notes[measure_number].sort(key=lambda x: (x.pos, 0 if x.lane in target_lanes else int(x.lane))) # Place targets at beginning
			start_measure = measure_number + self.insert_mes_offset # This is the real starting measure
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
							self.__parse_dict_make_measure(measure_number, note_collection, cur_note.pos - previous_note_time, not time_unchanged)
							# Reset notes and update time
							note_collection.clear()
							previous_hit_time = cur_note.pos
						note_collection.append(Note(cur_note.object, 0, cur_note.lane))
						time_unchanged = True
					elif time_unchanged:
						# Very similar to above but collapse
						self.__parse_dict_make_measure(measure_number, note_collection, cur_note.pos - previous_note_time, not time_unchanged)
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

	# Helper function for above that creates a measure at the number and inserts notes/stops from a dictionary.
	def __parse_dict_make_measure(self, measure_number, note_collection, pad_distance, collapse):
		print("Note collection", note_collection)
		assert(len(note_collection) != 0)
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
					((note.pos - prev_time) / self.mes_div) * (192 * self.maxbpm / self.normbpm), prev_time, self.mes_div)
				prev_time = note.pos
			new_measures[note.lane].add(note)
		# Add the stop for the padding distance
		self.bms.stop_add(measure_number + self.insert_mes_offset,
			(pad_distance / self.mes_div) * (192 * self.maxbpm / self.normbpm), prev_time, self.mes_div)
		print("Made measure at ", measure_number + self.insert_mes_offset)
		if collapse:
			self.bms.meters[measure_number + self.insert_mes_offset] = 1/1920
			print("Minimizing", measure_number + self.insert_mes_offset)
		self.insert_mes_offset += 1

	# Old version, not reccomended and buggy
	def parse_dict_old(self, r, pos_factor=0, nomove_target=False, make_on_end=False, target_lanes=Note.LANES_VISIBLE, minimize_lanes=True, check_dist_advance=False, move_all=False):
		stop_loc = 0
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

# This class contains tools for animations from images
class AnimationGimmick:
	import numpy
	import matplotlib.pyplot as plt
	import skimage.transform as transform

	def __init__(self, img):
		assert(type(img) == InsertMesGimmick)
		self.g = img

	# We are forced to a width of 8
	def frameToMineArray(self, frame, height=64, threshold=0.5):
		frame = self.transform.resize(frame, (height, 8), order=1)
		#frame_ = self.transform.resize(frame, (height, 8*8), order=0)
		#self.plt.imshow(frame_)
		#self.plt.show()

		mines = []
		# Make a mine if any position is over the threshold
		for x in range(8):
			for y in range(height):
				if any(channel > threshold for channel in frame[y][x]):
					mines.append([x, y])

		return mines