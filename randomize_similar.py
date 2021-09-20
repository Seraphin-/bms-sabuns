from gimmick import *
import sys
import os
import re
import random

assert(BMSparser.VERSION == '1.6')

if len(sys.argv) < 2:
	print("Please provide a BMS to edit")
	exit()

pattern = input("Input the pattern to match for the filename (ex. 'drum_[\\d+].wav'): ")
m = re.compile(pattern)
allowed = []

o = BMSparser(sys.argv[1])
for k, v in o.keysounds.items():
	if m.match(v) is not None:
		allowed.append(k)

print("Shuffling keysounds", allowed)

for measure in o.find(['*'], ['*']):
	for note in measure.notes:
		if note.object in allowed:
			note.object = random.choice(allowed)


directory, file = os.path.split(sys.argv[1])
base, ext = os.path.splitext(file)
print("Saving", os.path.join(directory, base + "_edited" + ext))
o.write_output(os.path.join(directory, base + "_edited" + ext))