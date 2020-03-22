from gimmick import *
assert(BMSparser.VERSION == '1.0')
from collections import defaultdict
from random import choice
from copy import deepcopy
from itertools import groupby

global insert_mes_offset, inserted_dict
insert_mes_offset = 0
inserted_dict = {}

MAX_BPM = 160000160
NORM_BPM = 160	

o = BMSparser('NewPeriod_sera.bme')

o.bpm_add(18, MAX_BPM, 0, 1)
all_notes = defaultdict(list)
MES_DIV=96
def makeDict(bms, measure):
	for n in measure.notes:
		all_notes[measure.number-insert_mes_offset].append(Note(n.object, (n.pos*MES_DIV)//measure.size, n.lane))
	bms.measures.remove(measure)

def parseDict(r, pos_factor=0, nomove_target=False, make_on_end=False, target_lanes=Note.LANES_VISIBLE):
	global insert_mes_offset, inserted_dict
	for k in r:
		all_notes[k].sort(key=lambda x: (x.pos, -int(x.lane))) # Push notes to front
		start = k+insert_mes_offset
		# We need to iterate through first to identify where we can start/end single measures. Ideally everything besides visible notes can be shoved into an 1/1920 measure
		target_indices = [i for i in range(len(all_notes[k])) if all_notes[k][i].lane in target_lanes]
		for i in range(len(all_notes[k])):
			newnote = Note(all_notes[k][i].object, all_notes[k][i].pos, all_notes[k][i].lane)
			stop_loc = newnote.pos
			if not nomove_target:
				if i in target_indices: # Push up once
					if i-1 not in target_indices: o.meters[k+insert_mes_offset] = 1/1920 #Bgm only measures
					insert_mes_offset += 1
					o.shift_indices(k+insert_mes_offset)
					if callable(pos_factor): newnote.pos = pos_factor(k, newnote)
					else: newnote.pos = int(newnote.pos*pos_factor)
					stop_loc = 0
				if i-1 in target_indices and i not in target_indices:
					o.meters[k+insert_mes_offset] = 1
					insert_mes_offset += 1
					o.shift_indices(k+insert_mes_offset)
			np = all_notes[k][i+1].pos if i != len(all_notes[k])-1 else MES_DIV
			m = Measure(MES_DIV, all_notes[k][i].lane, k+insert_mes_offset)
			m.add(newnote)
			o.add(m)
			if (np - all_notes[k][i].pos) != 0:
				o.stop_add(k+insert_mes_offset, ((np - all_notes[k][i].pos) / MES_DIV) * (192 * MAX_BPM / NORM_BPM), stop_loc, MES_DIV)
		o.meters[k+insert_mes_offset] = 1/1920 # last one too!
		if make_on_end:
			insert_mes_offset += 1
			o.shift_indices(k+insert_mes_offset)
			o.add(Measure(1, '01', k+insert_mes_offset))
		inserted_dict[k] = [start, k+insert_mes_offset]

def parseDictOldStretch(r):
	for k in r:
		offset = 0
		all_notes[k].sort(key=lambda x: x.pos)
		all_m = []
		stop_queue = []
		for i in range(len(all_notes[k])):
			np = all_notes[k][i+1].pos if i != len(all_notes[k])-1 else MES_DIV
			m = Measure(1, all_notes[k][i].lane, k+insert_mes_offset)
			all_m.append(m)
			m.add(Note(all_notes[k][i].object, i - offset, all_notes[k][i].lane))
			if (np - all_notes[k][i].pos) == 0:
				offset += 1
			else:
				stop_queue.append([((np - all_notes[k][i].pos) / MES_DIV) * (192 * MAX_BPM / NORM_BPM), i - offset])
		for m in all_m:
			m.size = len(all_notes[k]) - offset
			o.add(m)
		for s in stop_queue: o.stop_add(k+insert_mes_offset, s[0], s[1], len(all_notes[k]) - offset)
		o.meters[k+insert_mes_offset] = len(all_notes[k]) - offset

o.run(makeDict, range(18, 26), ['*'])
parseDict(range(18, 26))

num_patterns = [[ # Patterns are [lane, time]
	[3, 4], [4, 4], [5, 4],
	[3, 5], [5, 5], [3, 6], [5, 6],
	[3, 7], [5, 7], [3, 8], [5, 8],
	[3, 9], [4, 9], [5, 9],
], [
	[3, 4], [4, 4], [5, 4],
	[4, 5], [4, 6], [4, 7], [4, 8], [4, 9],
	[3, 8]
], [
	[3, 4], [4, 4], [5, 4],
	[3, 5], [3, 6],
	[4, 6], [5, 6],
	[5, 7], [5, 8], [3, 8],
	[4, 9]
], [
	[3, 4], [4, 4], [5, 4],
	[3, 6], [4, 6], [5, 6],
	[3, 7], [4, 7], [5, 7],
	[3, 9], [4, 9], [5, 9],
	[5, 5], [5, 8],
], [
	[3, 7], [4, 7], [5, 7],
	[3, 8], [4, 8],
	[4, 4], [4, 5], [4, 6], [4, 9]
], [
	[3, 4], [4, 4], [5, 4],
	[3, 6], [4, 6], [5, 6],
	[3, 7], [4, 7], [5, 7],
	[3, 9], [4, 9], [5, 9],
	[5, 5], [3, 8],
]]

TARGETS_FIRST = [[2],[4],[6],[1],[2],[4],[6],[6],[1]] 

def getNum(_, i, cur, targets, forced_offset=None):
	if i == 6:
		m = []
		for i in range(8):
			if i not in targets[cur] and i not in targets[cur+1]:
				for v in range(1, 32): m.append([i, v])
		return m
	m = [[targets[cur+1][0], v] for v in range(12,16) if (targets[cur] != targets[cur+1])]
	if forced_offset is not None:
		return [[n[0]+forced_offset, n[1]] for n in num_patterns[6-i]] + m
	if targets[cur] == [4]: #on 4
		return [[n[0]-2, n[1]] for n in num_patterns[6-i]] + m
	return deepcopy(num_patterns[6-i]) + m # We need to force a copy...

for i in range(18, 26):
	o.add_mines(inserted_dict[i], getNum, i-18, TARGETS_FIRST)


# Stream gimmick - use high bpm from earlier OK
all_notes.clear()
o.run(makeDict, range(26+insert_mes_offset, 34+insert_mes_offset), ['*'])
computed_notes_stream = defaultdict(list)
STREAM_FACTORS = [[1/3, 0, False], [1/4, 0, True], [1/5, 9, False], [1/6, 4, True], [1/7, 12, False], [1/8, 7, True], [1/9, 13, False], [1/10, 8, True]]

def playUpPlacements(mes, newnote):
	res = STREAM_FACTORS[mes-26][0]*newnote.pos + STREAM_FACTORS[mes-26][1]
	if STREAM_FACTORS[mes-26][2]: res = (MES_DIV//3) - res
	computed_notes_stream[mes].append([newnote.lane, int(res*2)])
	return int(res)

parseDict(range(26, 34), playUpPlacements)

def playUp(_, i, nxt, mes):
	notes = computed_notes_stream[mes][i:i+3]
	if i > 13:
		if mes == 33: notes += [['1' + str(note), 27] for note in nxt]
		else: notes += computed_notes_stream[mes+1][:(i+3)%16]
	return notes

for i in range(26, 33):
	o.add_mines(inserted_dict[i], playUp, [1], i, mul=96*2)
o.add_mines(inserted_dict[33], playUp, [1, 2], 33, mul=96*2)

MES_DIV=144
all_notes.clear()
#o.bpm_add(34, 160000000, 0, 1)
o.run(makeDict, range(34+insert_mes_offset, 38+insert_mes_offset), ['*'])
parseDict(range(34, 38), target_lanes=['11'])

TARGETS_SECOND = [[2,1], [4,1], [6,1], [6,1], [2,1]]
o.add_mines(inserted_dict[34], getNum, 0, TARGETS_SECOND, 0, target_lanes=['11'])
o.add_mines(inserted_dict[35], getNum, 1, TARGETS_SECOND, 2, target_lanes=['11'])
o.add_mines(inserted_dict[36], getNum, 2, TARGETS_SECOND, 0, target_lanes=['11'])
o.add_mines(inserted_dict[37], getNum, 3, TARGETS_SECOND, 0, target_lanes=['11'])

# Didn't use this in the end
# bpm_pattern_120 = [
# 	[1, 4], [2, 4], [3, 4], [5, 4], [6, 4], [7, 4],
# 	[1, 5], [5, 5], [7, 5],
# 	[1, 6], [2, 6], [3, 6], [5, 6], [7, 6],
# 	[1, 7], [2, 7], [3, 7], [5, 7], [7, 7],
# 	[3, 8], [5, 8], [7, 8],
# 	[1, 9], [2, 9], [3, 9], [5, 9], [6, 9], [7, 9],
# ]
# 
# bpm_pattern_160 = [
# 	[1, 4], [2, 4], [3, 4], [5, 4], [6, 4], [7, 4],
# 	[1, 5], [3, 5], [5, 5], [7, 5],
# 	[1, 6], [2, 6], [3, 6], [5, 6], [7, 6],
# 	[1, 7], [2, 7], [3, 7], [5, 7], [7, 7],
# 	[1, 8], [5, 8], [7, 8],
# 	[1, 9], [2, 9], [3, 9], [5, 9], [6, 9], [7, 9],
# ]
# 
# bpm_pattern_c = []
# for i in range(16):
# 	if i % 2 == 0: bpm_pattern_c += [[1, i], [3, i], [5, i], [7, i]]
# 	else: bpm_pattern_c += [[0, i], [2, i], [4, i], [6, i]]

MES_DIV=96

all_notes.clear()
o.bpm_add(40+insert_mes_offset, MAX_BPM, 0, 1)
o.run(makeDict, range(40+insert_mes_offset, 46+insert_mes_offset), ['*'])
parseDict(range(40, 46), nomove_target=True, make_on_end=True)

TARGETS_THIRD = [1,3,6,6,2,5,7]
REMAINING_THIRD = [[0,2,4,5,6,7],[0,2,4,5,7],[],[0,4,5,7],[0,4,7],[0,4]]
for i in range(40, 46):
	for j in range(40, i+1):
		if j == 43: continue #hacky but w/e
		if i == 42 and j == 42: continue
		lane = BMSparser._real_mine_lane(TARGETS_THIRD[j-40])
		m = Measure(64, lane, inserted_dict[i][1])
		o.add(m)
		start = 1 if i == j else 0
		if (j == 42 or j == 43) and (i == 42 or i == 43): start = 1
		for p in range(start, 64):
			m.add(Note(o.mine_damage, p))
	for j in REMAINING_THIRD[j-40]:
		m = Measure(4, BMSparser._real_mine_lane(j), inserted_dict[i][1])
		o.add(m)
		m.add(Note(o.mine_damage, 1))

MES_DIV=64
all_notes.clear()
o.bpm_add(62+insert_mes_offset, MAX_BPM, 0, 1)
o.run(makeDict, [62+insert_mes_offset], ['*'])
parseDict([62])

letter_pattern = o.convert_pat_string("""XXOOXXX
XOXOXOX
XOXOXXX
XOXOXOO
XOXOXOO
OOOOOOO
XXXOXXX
XOOOXOO
XXXOXXX
OOXOXOO
XXXOXXX
OOOOOOO
XXOOOXO
XOXOXOX
XXOOXXX
XOXOXOX""")

def revealUp(mes, i):
	if i == 0: return []
	if i == 16:
		return [[l, i] for l in [1,3,5,6,7] for i in range(0,32,2)]
	l = list(filter(lambda x: x[1] <= i, letter_pattern))
	return l + [[0, 16], [2, 16], [0, 17], [2, 17]]

o.add_mines(inserted_dict[62], revealUp)

all_notes.clear()
o.run(makeDict, range(63+insert_mes_offset, 79+insert_mes_offset), ['*'])
parseDictOldStretch(range(63, 79))

global last_i, explosion_counter, targets
last_i = None
explosion_counter = []
targets = [[[0, 2, 4], ['12']], [[3, 5], ['13']], [[4, 6], ['14']], [[4, 6], ['14']],
[[1, 3], ['11']], [[2, 6], ['12']], [[5, 7], ['15']], [[5, 7], ['15']],
[[1, 4, 0], ['11']], [[2, 6], ['12']], [[4, 7], ['14']], [[4, 7], ['14']],
[[1, 5], ['11']], [[2, 6], ['12']], [[3, 7], ['13']], [[3, 7], ['13']], [[1, 2, 0], None]]
def explosion(mes, i, sources, first=False):
	last = i == 4
	mes -= insert_mes_offset
	global last_i, explosion_counter, targets
	if last_i != i:
		explosion_counter.append([sources, 0]) #preserve across measures
		last_i = i
	mines = []
	remove = []
	for ec_index in range(len(explosion_counter)):
		if explosion_counter[ec_index][1] > 22:
			remove.append(ec_index)
			continue
		explosion_counter[ec_index][1] += 1
		if explosion_counter[ec_index][1] == 1: continue
		for s in explosion_counter[ec_index][0]:
			for cur in range(-(explosion_counter[ec_index][1]), explosion_counter[ec_index][1]+1):
				if s + cur < 0 or s + cur > 7: continue
				if s + cur in sources: continue
				if explosion_counter[ec_index][1] - abs(cur) > MES_DIV: continue
				pair = [s + cur, explosion_counter[ec_index][1] - abs(cur) - 1]
				if (last and pair[0] in targets[mes+1-63][0]) or (first and pair[0] in targets[mes-63][0]): continue
				if pair not in mines and pair[1] >= 0: mines.append(pair)
	for idx in remove: explosion_counter.pop(idx) #do out of loop  
	# Next preview
	if targets[mes+1-63][0] == targets[mes-63][0] or last or first: return mines
	for t in targets[mes+1-63][0]:
		if [t, 10] not in mines: mines.append([t, 10])
	return mines

for mes in range(63, 79):
	o.add_mines_stretched(mes+insert_mes_offset, explosion, targets[mes - 63][0], target_lane=targets[mes-63][1])

all_notes.clear()
o.bpm_add(83+insert_mes_offset, MAX_BPM, 0, 1)
o.run(makeDict, [83+insert_mes_offset], ['*'])
parseDict([83], target_lanes=['04'])

letter_pattern2_raw = """OOOOOOO
XXXOXOX
OXOOOXO
OXOOOXO
OXOOOXO
OXOOOXO
OOOOOOO
XXXXXXX
OOOOOOO
XXXOXXX
XOOOXOX
XXXOXXX
XOOOXOO
XOOOXOO
OOOOOOO
OOOOOOO"""
letter_pattern2 = o.convert_pat_string(letter_pattern2_raw)
letter_pattern2_empty = o.convert_pat_string(letter_pattern2_raw, yes='O') #inverted

def revealRemove(mes, i):
	if len(letter_pattern2) > 0 and i > 5: letter_pattern2.remove(choice(letter_pattern2))
	return letter_pattern2 + letter_pattern2_empty

o.add_mines(inserted_dict[83], revealRemove, target_lanes=['*'])
o.optimize()
o.write_output('NewPeriod_sera_g2.bme')