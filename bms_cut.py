import argparse
import wave

parser = argparse.ArgumentParser(description='Cut up a wav file on beats based on interval.')
parser.add_argument('infile', action='store', type=str)
parser.add_argument('outbase', action='store', type=str)
parser.add_argument('bpm', action='store', type=float)
parser.add_argument('interval', action='store', type=int)
parser.add_argument('--length', '-l', action='store', type=int, default=-1)

args = parser.parse_args()

original = wave.open(args.infile, 'rb')
fr = original.getframerate()
nf = original.getnframes()
nc = original.getnchannels()
sw = original.getsampwidth()
each = int(fr/(args.bpm/60)/(args.interval/4))
print(each)
if args.length == -1:
	args.length = int(nf // each)

for i in range(args.length+1):
	if i == args.length:
		each = nf - (each * args.length)
	audio = original.readframes(each)
	new = wave.open(args.outbase + "%.2d" % i + '.wav', 'wb')
	new.setnchannels(nc)
	new.setnframes(each)
	new.setframerate(fr)
	new.setsampwidth(sw)
	new.writeframes(audio)
	new.close()
	print("Wrote", args.outbase + "%.2d" % i + '.wav')