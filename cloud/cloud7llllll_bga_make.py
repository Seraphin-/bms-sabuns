from gimmick import *
from collections import defaultdict
assert(BMSparser.VERSION == '1.2')

# uX7n2YZC8i

o = BMSparser('cloud7llllll_bga.bme', enc='cp932')
g = InsertMesGimmick(o, 193000193, 193, 32*3)

def duplicateMeasureMines(mes):
	o.shift_indices(mes+g.insert_mes_offset)
	o.meters[mes+g.insert_mes_offset] = 2
	g.add_max(mes)
	mine_dict = {}
	for measure in o.find([mes+g.insert_mes_offset+1], Note.LANES_VISIBLE + Note.LANES_LN):
		notes_visible = []
		notes_ln = []
		for note in measure.notes:
			if note.lane in Note.LANES_VISIBLE: notes_visible.append(note)
			else: notes_ln.append(note)
		for note in notes_visible:
			if note.lane[1] not in mine_dict:
				m = Measure(32, 'D' + note.lane[1], mes+g.insert_mes_offset)
				mine_dict[note.lane[1]] = m
				o.add(m)
			mine_dict[note.lane[1]].add(Note(o.mine_damage, int((note.pos / measure.size) * 16 + 1)))
		# We will assume ln starts/ends in measure
		# First find LN pairs, sort by time
		notes_ln.sort(key=lambda x: x.pos)
		ln_pairs = defaultdict(list)
		for note in notes_ln:
			if note.lane in ln_pairs:
				if ln_pairs[note.lane][-1][1] == -1:
					ln_pairs[note.lane][-1][1] = int((note.pos / measure.size) * 16)
					continue
			ln_pairs[note.lane].append([int((note.pos / measure.size) * 16), -1])
		for lane, pairs in ln_pairs.items():
			for pair in pairs:
				if lane[1] not in mine_dict:
					m = Measure(32, 'D' + lane[1], mes+g.insert_mes_offset)
					mine_dict[lane[1]] = m
					o.add(m)
				for time in range(pair[0], pair[1]+1):
					mine_dict[lane[1]].add(Note(o.mine_damage, time + 1))

	g.insert_mes_offset += 1
	g.add_norm(mes)

for i in range(19, 51):
	duplicateMeasureMines(i)


# Make visual 321 effect

g.add_max(68)
g.run_adjusted(68, 76, ['*'])
g.parse_dict(range(68, 76), target_lanes=['01'])

high_pattern_raw = {
	'61': [5, 1*6],
	'62': [3, 2*6],
	'63': [2, 3*6],
	'64': [4, 2*6],
	'65': [3, 3*6],
	'66': [2, 4*6],
	'67': [6, 1*6],
	'68': [5, 2*6],
	'69': [3, 3*6],
	'6A': [5, 1*6],
	'6B': [4, 2*6],
	'6C': [3, 3*6],
	'6D': [6, 4*6],
	'6E': [5, 5*6],
	'6F': [3, 6*6],
	'70': [5, 5*6],
	'71': [3, 6*6],
	'72': [1, 7*6]
}
high_pattern = {}
for k, v in high_pattern_raw.items():
	effect = [[v[0], v[1]+3],
	[v[0]-1, v[1]+1], [v[0], v[1]+1], [v[0]+1, v[1]+1],
	[v[0]-1, v[1]+2], [v[0], v[1]+2], [v[0]+1, v[1]+2],
	[v[0]-2, v[1]], [v[0]-1, v[1]], v, [v[0]+1, v[1]], [v[0]+2, v[1]],
	[v[0]-1, v[1]-1], [v[0], v[1]-1], [v[0]+1, v[1]-1],
	[v[0]-1, v[1]-2], [v[0], v[1]-2], [v[0]+1, v[1]-2],
	[v[0], v[1]-3]]
	high_pattern[k] = effect
for k, v in high_pattern.items():
	for mine in v:
		if mine[0] < 0 or mine[0] > 7: v.remove(mine)
		else: mine[0] = 'D' + BMSparser._real_lane(mine[0])

internal_counter_obj = '61'

def revealRemove(mes, i, real_mes_no):
	global internal_counter_obj, internal_counter_last_0d
	if mes[0].number in o.meters and o.meters[mes[0].number] != 1: return []
	# is there a note to actually change on?
	for note in {n for m in mes for n in m.notes}:
		if note.object in high_pattern:
			internal_counter_obj = note.object
		if note.object == '0D':
			internal_counter_last_0d = -1
	internal_counter_last_0d += 1
	if real_mes_no >= 72:
		pattern_copy = []
		for y_pos in range(internal_counter_last_0d*30, g.mes_div):
			for x_pos in range(8): pattern_copy.append(['D' + BMSparser._real_lane(x_pos), y_pos])
		return [item for item in pattern_copy if item not in high_pattern[internal_counter_obj]] \
			+ [item for item in high_pattern[internal_counter_obj] if item[1] < internal_counter_last_0d*30]
	return high_pattern[internal_counter_obj]

for i in range(68, 76):
	o.add_mines(g.inserted_dict[i], revealRemove, i, target_lanes=['01'], mul=g.mes_div)

# Already normal on 76
	
for i in range(78, 110):
	duplicateMeasureMines(i)

o.optimize()
o.write_output('cloud7llllll_bga_.bme', enc='cp932')