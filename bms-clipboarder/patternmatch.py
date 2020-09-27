cols = []
for line in open('match1.txt', 'r'):
	if line.rstrip() == 'iBMSC Clipboard Data xNT':
		continue
	cols.append(line.split(' ')[0])

print('iBMSC Clipboard Data xNT', end='')
ci = 0
for line in open('match2.txt', 'r'):
	if line.rstrip() == 'iBMSC Clipboard Data xNT':
		continue
	print()
	n = line.rstrip().split(' ')
	n[0] = cols[ci]
	ci += 1
	ci %= len(cols)
	print(' '.join(n), end='')