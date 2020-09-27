cols = {}
for line in open('match1.txt', 'r'):
	if line.rstrip() == 'iBMSC Clipboard Data xNT':
		continue
	s = line.split(' ')
	cols[s[2]] = s[0]

print('iBMSC Clipboard Data xNT', end='')
for line in open('match2.txt', 'r'):
	if line.rstrip() == 'iBMSC Clipboard Data xNT':
		continue
	print()
	n = line.rstrip().split(' ')
	if n[2] in cols:
		n[0] = cols[n[2]]
	print(' '.join(n), end='')