cols = {}
for line in open('match1.txt', 'r'):
	if line == 'iBMSC Clipboard Data xNT\r\n':
		continue
	s = line.split(' ')
	cols[s[2]] = s[0]

print('iBMSC Clipboard Data xNT')
for line in open('match2.txt', 'r'):
	if line == 'iBMSC Clipboard Data xNT\r\n':
		continue
	n = line.rstrip().split(' ')
	if n[2] in cols:
		n[0] = cols[n[2]]
	print(' '.join(n))