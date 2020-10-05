from gimmick import *
assert BMSparser.VERSION == '1.3'

o = BMSparser('lime_stargazer_randomizer.bme')

# Dupe measures
# Inclusive, start, end
insert_offset = 0
dupeMeasures = [[13, 15, 1], [29, 32, 1], [37, 40, 1], [41, 44, 3], [45, 52, 3]]

for start, end, count in dupeMeasures:
	for _ in range(count):
		o.shift_indices(end+insert_offset+1, end - start + 1)
		for measure in o.find(range(start+insert_offset, end+insert_offset+1), ['*']):
			newmes = Measure.clone(measure)
			newmes.number = measure.number + end - start + 1
			o.add(newmes)
		insert_offset += end - start + 1

# Randomize!
randomize(o, 1, 9, 16)
randomize(o, 13, 100, 16)

o.optimize()
o.write_output('lime_stargazer_randomizer_.bme')
