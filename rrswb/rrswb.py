# Clean ZZ notes when possible with priority order

from gimmick import *
assert(BMSparser.VERSION == '1.1')

PRIORITY = ['58', '59', '5A', '5B', '68', '69', '6A', '6B', '78', '79', '7A', '7B', '12', '16', '15', '11', '17']

o = BMSparser('rrswb_7s_i_orig.bme')
for measure in o.find(['*'], Note.LANES_VISIBLE):
	for note in measure.notes:
		if note.object == 'ZZ':
			fd = o.find([measure.number], ['01'])
			for target_measure in fd: #take from bgm
				for pos in PRIORITY:
					target = list(filter(lambda x: x.object == pos and (note.pos/measure.size) == (x.pos/target_measure.size), target_measure.notes))
					if len(target) == 1:
						note.object = target[0].object
						target_measure.notes.remove(target[0])
						break
				else: continue
				break
			else:
				for target_measure in fd:
					target = list(filter(lambda x: (note.pos/measure.size) == (x.pos/target_measure.size), target_measure.notes))
					if len(target) >= 1:
						note.object = target[0].object
						target_measure.notes.remove(target[0])
						break

o.optimize()
o.write_output('rrswb_7s_i.bme')