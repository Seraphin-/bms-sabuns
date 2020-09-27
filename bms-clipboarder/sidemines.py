import sys
from collections import defaultdict

print('ok')
print('Moved notes!')
print('iBMSC Clipboard Data xNT')

first = True
used = defaultdict(set)
times = set()

for line in sys.stdin:
	if first:
		first = False
		continue
	print(line, end='')
	l2 = line.split(' ')
	used[l2[1]].add(l2[0])
	times.add(l2[1])
print()

for time in times:
	for pos in range(6, 13):
		if str(pos) not in used[time]:
			print('%s %s 10000 0 0 -1' % (pos, time))