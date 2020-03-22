from gimmick import *
assert(BMSparser.VERSION == '1.1')

o = BMSparser('groundbreaker7_sera.bme')
g = InsertMesGimmick(o, 158000158, 158, 32*3)

def duplicateMeasureMines(mes):
	o.shift_indices(mes+g.insert_mes_offset)
	g.add_max(mes)
	mine_dict = {}
	for measure in o.find([mes+g.insert_mes_offset+1], Note.LANES_VISIBLE):
		for note in measure.notes:
			if note.lane not in mine_dict:
				m = Measure(measure.size, 'D' + BMSparser._real_lane(BMSparser._lane_no(note.lane)-1), mes+g.insert_mes_offset)
				mine_dict[note.lane] = m
				o.add(m)
			mine_dict[note.lane].add(Note(o.mine_damage, note.pos))
	g.insert_mes_offset += 1
	g.add_norm(mes)

duplicateMeasureMines(17)
duplicateMeasureMines(21)

g.add_max(25)

g.run_adjusted(25, 33, ['*'])
g.parse_dict(range(25, 33), pos_factor=0)

""
new_offset = 0
targets = {}
for i in range(25, 33):
	targets[i] = [n for n in g.all_notes[i] if n.lane in Note.LANES_VISIBLE]
for i in range(25, 33):
	prev_pos = [0]
	j = 0
	has_real_zero = False
	for mes in range(g.inserted_dict[i][0], g.inserted_dict[i][1]):
		for measure in o.find([mes+new_offset], Note.LANES_VISIBLE):
			# Only expect one per now
			assert(len(measure.notes) == 1)
			if targets[i][j].pos == 0:
				has_real_zero = True
			prev_pos.append(targets[i][j].pos)
			for idx in range(1, len(prev_pos)):
				o.shift_indices(mes+new_offset)
				g.insert_mes_offset += 1
				new_offset += 1
				o.meters[mes+new_offset-1] = ((prev_pos[idx]-prev_pos[idx-1])/3/g.mes_div)
				if (has_real_zero and idx != 1) or idx != 1:
					for lane in range(4):
						m = Measure(1, 'D'+ BMSparser._real_lane(lane), mes+new_offset-1)
						m.add(Note(o.mine_damage, 0))
						o.add(m)
			for idx in range(len(prev_pos), len(targets[i])):
				for lane in range(5, 8):
					m = Measure(g.mes_div, 'D'+ BMSparser._real_lane(lane), mes+new_offset)
					m.add(Note(o.mine_damage, (targets[i][idx].pos-targets[i][j].pos)//3))
					o.add(m)
			if i != 32:
				for lane in range(5, 8):
					m = Measure(g.mes_div, 'D'+ BMSparser._real_lane(lane), mes+new_offset)
					nxt = g.all_notes[i+1][0]
					m.add(Note(o.mine_damage, (g.mes_div+targets[i+1][0].pos-targets[i][j].pos)//3))
					o.add(m)
			j += 1

g.add_norm(33)

g.add_max(41)
g.run_adjusted(41, 49, ['*'])

computed_notes = g.defaultdict(list)
def playUpPlacements(mes, newnote):
	newnote.pos = int(newnote.pos * (1/3))
	newnote.lane = '5' + newnote.lane[1]
	computed_notes[mes].append(newnote)

g.parse_dict(range(41, 49), pos_factor=playUpPlacements)
END_PAT_STRING = """XOX|XOX
OXO|OXO
XOX|XOX
OXO|OXO
XOX|XOX
OXO|OXO
XOX|XOX
OXO|OXO
XOX|XOX
OXO|OXO
XOX|XOX
OXO|OXO
XOX|XOX
OXO|OXO
XOX|XOX
OXO|OXO"""
END_PAT_1 = o.convert_pat_string(END_PAT_STRING, yes='X', mn=16, offset=24)
END_PAT_2 = o.convert_pat_string(END_PAT_STRING, yes='O', mn=16, offset=24)

def playUp(targets, i, mes, off_lanes=None, make_ln=True):
	notes = []
	# targets will only be len(1) for this
	if make_ln:
		assert(len(targets[0].notes) == 1)
		targets[0].add(Note(targets[0].notes[0].object, g.mes_div-1, '5' + targets[0].notes[0].lane[1]))
	for idx in computed_notes[mes]:
		if mes in range(41, 49):
			for j in off_lanes:
				if i-1 != j: notes.append([j, idx.pos])
		if mes in range(50, 66):
			notes.append(['D' + BMSparser._real_lane(BMSparser._lane_no(idx.lane)-1), idx.pos]) #cur meas
	if mes in range(50, 65):
		notes.append(['D' + BMSparser._real_lane(BMSparser._lane_no(computed_notes[mes+1][0].lane)-1), computed_notes[mes+1][0].pos+32])
	if mes == 48:
		if i % 2 == 0: notes += END_PAT_1
		else: notes += END_PAT_2
	return notes

for i in range(41, 49):
	o.add_mines(g.inserted_dict[i], playUp, i, [0,1,2,3,5,6,7], mul=g.mes_div, target_lanes=Note.LANES_LN)

g.add_norm(49)

for i in [0,1,2,3,5,6,7]:
	lane = 'D' + BMSparser._real_lane(i)
	m = Measure(g.mes_div, lane, 49+g.insert_mes_offset)
	for p in range(g.mes_div):
		m.add(Note(o.mine_damage, p))
	o.add(m)
g.add_max(50)

g.run_adjusted(50, 66, ['*'])
g.parse_dict(range(50, 58), pos_factor=playUpPlacements)

def addComputedNote(mes, newnote):
	newnote.pos = int(newnote.pos * (1/3))
	computed_notes[mes].append(Note.clone(newnote))
	newnote.pos = g.mes_div-1

g.parse_dict(range(58, 66), pos_factor=addComputedNote)

for i in range(50, 58):
	o.add_mines(g.inserted_dict[i], playUp, i, mul=g.mes_div, target_lanes=Note.LANES_LN)

for i in range(58, 66):
	o.add_mines(g.inserted_dict[i], playUp, i, None, False, mul=g.mes_div)

g.add_norm(66) #58

"""g.run_adjusted(72, 75, ['*'])

for k in range(72, 75):
	g.all_notes[k].sort(key=lambda x: (x.pos, -int(x.lane))) # Push notes to front
	start = k+g.insert_mes_offset
	for i in range(len(g.all_notes[k])):
		newnote = Note(g.all_notes[k][i].object, 0, g.all_notes[k][i].lane)
		np = g.all_notes[k][i+1].pos if i != len(g.all_notes[k])-1 else g.all_notes[k][i].pos #g.mes_div
		m = Measure(g.mes_div, newnote.lane, k+g.insert_mes_offset)
		m.add(newnote)
		g.bms.add(m)
		if np - g.all_notes[k][i].pos != 0:
			g.bms.meters[k+g.insert_mes_offset] = (np - g.all_notes[k][i].pos) / g.mes_div
			g.insert_mes_offset += 1
			g.bms.shift_indices(k+g.insert_mes_offset)
		g.bms.meters[k+g.insert_mes_offset] = (g.mes_div - g.all_notes[k][i].pos) / g.mes_div
	g.inserted_dict[k] = [start, k+g.insert_mes_offset]
#g.add_norm(74)"""
# No space :(

g.add_max(74)
g.add_norm(76)
o.stop_add(75+g.insert_mes_offset, 9600000, 0, 1)
o.stop_add(76+g.insert_mes_offset, 192, 0, 1)

mine_mes = {}
for i in range(128):
	for j in range(8):
		if j not in mine_mes:
			mine_mes[j] = Measure(128, 'D' + BMSparser._real_lane(j), 76+g.insert_mes_offset)
			o.add(mine_mes[j])
		mine_mes[j].add(Note(o.mine_damage, i))

o.measures.sort(key=lambda m: m.number)
o.optimize()
o.write_output('groundbreaker7_sera_g.bme')
