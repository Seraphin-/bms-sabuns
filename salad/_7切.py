from gimmick import *
from random import randrange
from numpy import lcm
assert(BMSparser.VERSION == '1.4')

o = BMSparser('_7切_.bms')

g = InsertMesGimmick(o, 177177, 177, 16)

oi = {}
def addSkips(mes):
	for scrMeasure in o.find([mes+g.insert_mes_offset], ['16']):
		# o.meters[mes] = 1 + len(scrMeasure.notes) / (32+len(scrMeasure.notes))
		o.meters[mes] = 1 + len(scrMeasure.notes) / 32
		if scrMeasure.size < 32:
			o._reindex_measure(scrMeasure, 32)
		scrMeasure.size += len(scrMeasure.notes)
		for i in range(len(scrMeasure.notes)):
			scrMeasure.notes[i].pos += i
		for scr in scrMeasure.notes:
			for measure in o.find([mes+g.insert_mes_offset], ['*']):
				if measure.lane == '16': continue
				if id(measure) not in oi:
					lcmv = lcm(32, measure.size)
					oi[id(measure)] = lcmv // 32
					o._reindex_measure(measure, lcmv)
				measure.size += oi[id(measure)]
				for note in measure.notes:
					if note.pos >= (scr.pos * oi[id(measure)]):
						note.pos += oi[id(measure)]
			o.bpm_add(mes+g.insert_mes_offset, g.maxbpm, scr.pos, scrMeasure.size)
			o.bpm_add(mes+g.insert_mes_offset, g.normbpm, scr.pos+1, scrMeasure.size)

for i in range(27, 43):
	addSkips(i)

BASE_MES = 101
g.add_max(BASE_MES)

for _ in range(32):
	# Pick 10 random measure points
	points = sorted(set([randrange(32) for _ in range(10)]))
	o.shift_indices(BASE_MES+1+g.insert_mes_offset, len(points)+2)

	cur = 0
	for i, point in enumerate(points, 1):
		o.meters[BASE_MES+g.insert_mes_offset+i] = (point - cur) / 196
		cur = point

	o.meters[BASE_MES+g.insert_mes_offset] = (points[0] + 24) / 196
	# o.meters[BASE_MES+g.insert_mes_offset+len(points)+1] = (196 - points[-1] + 24) / 196
	# Actually, 1 is fine
	o.stop_add(BASE_MES+g.insert_mes_offset, (192/32/4) * g.maxbpm / g.normbpm, 0, 1)

	g.insert_mes_offset += len(points)+2	 # should it be 11? we can probably get it to that way but yeah

g.add_norm(BASE_MES+1)
o.optimize()
o.write_output('_7切.bms')