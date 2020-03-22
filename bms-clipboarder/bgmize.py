import sys
from collections import defaultdict

print('ok')
print('Moved notes!')
print('iBMSC Clipboard Data xNT')

first = True
used = defaultdict(int)
base = 27

for line in sys.stdin:
	if first:
		first = False
		continue
	l2 = line.replace('\r\n', '\n').split(' ')
	l2[0] = str(base + used[l2[1]])
	used[l2[1]] += 1
	print(' '.join(l2), end='')