from gimmick import *
from collections import defaultdict
assert(BMSparser.VERSION == '1.2')
# LR2 friendly version

o = BMSparser('cloud7llllll_bga.bme', enc='cp932')
g = InsertMesGimmick(o, 1930193, 193, 32*3)

def duplicateMeasureMines(mes):
	o.meters[mes+g.insert_mes_offset-1] = 17/16 # Skip 1/16 at the tail
	for measure in o.find([mes+g.insert_mes_offset-1], ['*']):
		if measure.size % 16 != 0:
			# We need to reindex the measure to lcm(measure.size, 16)
			o._reindex_measure(measure, 16)
		measure.size += measure.size // 16
	o.bpm_add(mes+g.insert_mes_offset-1, g.maxbpm, 16, 17)
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
o.write_output('cloud7llllll_bga_notmoyash.bme', enc='cp932')