cols = []
for line in open('match1.txt', 'r'):
	if line == 'iBMSC Clipboard Data xNT\r\n':
		continue
	cols.append(line.split(' ')[0])

print('iBMSC Clipboard Data xNT')
ci = 0
for line in open('match2.txt', 'r'):
	if line == 'iBMSC Clipboard Data xNT\r\n':
		continue
	n = line.rstrip().split(' ')
	n[0] = cols[ci]
	ci += 1
	ci %= len(cols)
	print(' '.join(n))