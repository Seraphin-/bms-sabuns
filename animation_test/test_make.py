from gimmick import *
from collections import defaultdict
from PIL import Image, ImageSequence
import numpy as np
assert(BMSparser.VERSION == '1.3')

o = BMSparser('test.bms', enc='cp932')

g = InsertMesGimmick(o, 0, 0, 64)
a = AnimationGimmick(g)

mines = []
im = Image.open("S9Ab.gif")
for frame in ImageSequence.Iterator(im):
	mines.append(a.frameToMineArray(np.array(frame.convert('RGB')), threshold=0.02))

for idx in range(40*4):
	ml = {}
	o.stop_add(idx, 12*100000/6, 0, 1)
	for j in mines[idx%40]:
		j[0] = 'D' + BMSparser._real_lane(j[0])
		if j[0] not in ml:
			m = Measure(128, j[0], idx)
			ml[j[0]] = m
			o.add(m)
		ml[j[0]].add(Note(o.mine_damage, j[1], j[0]))

o.optimize()
o.write_output('test_.bme', enc='cp932')