from gimmick import *
import random
import itertools

o = BMSparser("_SERA_.bms")
offset = 0

BDIV = 64
counter = 0
norm_bpm = 130
v_pos = [32] * 8
for mes in range(16):
    if mes not in o.meters:
        o.meters[mes] = 1
    c_len = int(BDIV * o.meters[mes])
    o.meters[mes] *= BDIV

    # For mines
    mine_mes = []
    for i in range(8):
        mine_mes.append(Measure(c_len*BDIV*2, 'D' + BMSparser.real_lane(i), mes))
        o.add(mine_mes[i])

    for i in range(c_len):
        # Lazy shit
        if mes == 4:
            if i == 0:
                norm_bpm = 140
            if i == 32:
                norm_bpm = 150
        if mes == 5:
            if i == 0:
                norm_bpm = 160
            if i == 32:
                norm_bpm = 170
        if mes == 6:
            if i == 0:
                norm_bpm = 180
            if i == 32:
                norm_bpm = 190
        if mes == 7:
            if i == 0:
                norm_bpm = 200
            if i == 32:
                norm_bpm = 210
        if mes == 8:
            if i == 0:
                norm_bpm = 220
            if i == 32:
                norm_bpm = 230
        if mes == 9:
            if i == 0:
                norm_bpm = 240
            if i == 32:
                norm_bpm = 250
        if mes == 10:
            if i == 0:
                norm_bpm = 260
            if i == 32:
                norm_bpm = 270
        if mes == 11:
            if i == 0:
                norm_bpm = 280
            if i == 32:
                norm_bpm = 280
        this_bpm = 1800000 + round(999*(counter/1038)**2)
        counter += 1

        # Mine anim
        ia = round(20 * (counter / 1038) ** 2)
        for ii in range(8):
            v_pos[ii] += int(ia * (1 if ii % 2 == 0 else -1) * (1+random.randrange(10)*.025))
            v_pos[ii] %= BDIV
            mine_mes[ii].add(Note('01', BDIV*i*2 + v_pos[ii]))

        o.bpm_add(mes, this_bpm, i, c_len)
        o.stop_add(mes, round((this_bpm / norm_bpm) * (192 / BDIV)), i, c_len)

this_bpm = 180

real_notes = [("17", BDIV//4), ("18", BDIV//4), ("19", 0), ("1A", 0)]
bpm_list = [180, 180, 190, 200]
for mes in range(16, 24, 2):
    cidx = (mes-16)//2
    this_bpm = bpm_list[cidx]
    o.shift_indices(mes+offset+1, 16)
    cbpm = 1800000 + this_bpm
    o.bpm_add(mes+offset, cbpm, 0, 1)

    for i in range(4):
        o.meters[mes+i*4+offset] = 1/16
        o.meters[mes+i*4+offset+2] = 1/16
        o.stop_add(mes+offset+i*4+2, round((cbpm / this_bpm) * (192 * 7 / 32)), 0, 1)
        o.stop_add(mes+offset+i*4, round((cbpm / this_bpm) * (192 / 32)), 0, 1)

        o.ignored_lines.append("#RANDOM 7\n")
        for r in range(1, 8):
            m = Measure(BDIV, 'D' + BMSparser.real_lane(r), mes+i*4+offset+4)
            for p in range(real_notes[cidx][1], BDIV-8):
                m.add(Note('01', p))
            o.ignored_lines.append("#IF %d\n" % r)
            o.ignored_lines.append(m.get_string() + '\n')
            o.ignored_lines.append("#ENDIF\n")
            if i == 3:
                m = Measure(BDIV, '5' + BMSparser.real_lane(r), mes + 18 + offset)
                sound, pos = real_notes[cidx]
                m.add(Note(sound, pos))
                m.add(Note(sound, BDIV - 8))
                o.ignored_lines.append("#IF %d\n" % r)
                o.ignored_lines.append(m.get_string() + '\n')
                o.ignored_lines.append("#ENDIF\n")
        o.ignored_lines.append("#ENDRANDOM\n")

    o.meters[mes + 16 + offset] = 1 / 16
    o.bpm_add(mes + 16 + offset, this_bpm, 0, 1)
    o.stop_add(mes + 16 + offset, 12, 0, 1)

    offset += 16

# 32~

# 48~
# allotted is 15x16th of 240, 07 after a 4th (4x)
o.shift_indices(48+offset, BDIV - 4 - 16)
pattern = [1, 2, 3, 4, 5, 1, 2, 3, 5, 6, 7, 3, 4, 5, 6, 7]
for i in range(BDIV-4):
    o.meters[48+offset+i] = 2
    if i == 16:
        m = Measure(1, Note.LANE_BGM, 48+offset+i)
        o.add(m)
        m.add(Note('07', 0))

    o.stop_add(48+offset + i, round((1800240 / 240) * (192 / 64)), ((BDIV-i-6) % BDIV), BDIV*2)
    # Notes matching real
    mine_mes = [Measure(BDIV*2, 'D' + BMSparser.real_lane(ll), 48 + offset + i) for ll in range(8)]
    [o.add(m) for m in mine_mes]
    for n in range(16):
        note = pattern[n]
        mine_mes[note].add(Note('01', n*4))

offset += BDIV - 4 - 16

o.shift_indices(70+offset+1, 63)
o.bpm_add(70+offset, 1800065, 0, 1)
real_notes = [(3, 0), (4, 2), (5, 4), (6, 6), (7, 8), (0, 8)]  # lane, time
ok_lanes = [0, 2, 3, 4, 5, 6, 7]
for i in range(64):
    this_mes = 70+offset+i
    o.stop_add(this_mes, round((1800065 / 65) * (192 / 128)), 0, 1)
    o.meters[this_mes] = 1

    mine_mes = [Measure(256, 'D' + BMSparser.real_lane(ll), this_mes) for ll in range(8)]
    [o.add(m) for m in mine_mes]
    if i % 2 == 0:
        bgm_mes = Measure(1, Note.LANE_BGM, this_mes)
        bgm_mes.add(Note('9T', 0))
        o.add(bgm_mes)

    if i > 60 or i < 1:
        continue

    # Real notes
    for lane, time in real_notes:
        mine_mes[lane].add(Note('01', 128+time*4-i*2))

    # Random mines...?
    for lane in ok_lanes:
        for ii in range(16):
            try:
                mine_mes[lane].add(Note('01', i % 16 + ii*16))
            except ValueError:  # overlapping real
                pass

    for _ in range(40):
        try:
            mine_mes[random.choice(ok_lanes)].add(Note('01', random.randrange(256)))
        except ValueError:
            pass

offset += 63

# 76~
# Write out randomness
nums = [[
    "0000000000000000000000000101010000000000000000010101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000101010101010101010101010101010100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000101010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
], [
    "0000000000000000000000000101010101010100000000010101010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000101010000010101010000000001010100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000101010000000001010101010101010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
], [
    "0000000000000000000000000001010101000000000000010101010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000101010000000101010100000001010100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000001010101010100000101010101010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
], [
    "0000000000000000000000000000000000000101010101010101010100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000000000000000101010100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000101010101010101010101010101010100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
]]

o.ignored_lines.append("#RANDOM 24\n")
for idx, perm in enumerate(itertools.permutations(range(4))):
    o.ignored_lines.append("#IF %d\n" % (idx+1))
    o.ignored_lines.append("#%03dD3:%s%s%s%s\n" % (77+1+offset, nums[perm[0]][0], nums[perm[1]][0], nums[perm[2]][0], nums[perm[3]][0]))
    o.ignored_lines.append("#%03dD4:%s%s%s%s\n" % (77+1+offset, nums[perm[0]][1], nums[perm[1]][1], nums[perm[2]][1], nums[perm[3]][1]))
    o.ignored_lines.append("#%03dD5:%s%s%s%s\n" % (77+1+offset, nums[perm[0]][2], nums[perm[1]][2], nums[perm[2]][2], nums[perm[3]][2]))
    o.ignored_lines.append("#ENDIF\n")
o.ignored_lines.append("#ENDRANDOM\n")

# 90~
real_notes = [None, 2, 7, 5, 6]
bpm_list = [170, 160, 150, 141, 122]
for mes in range(90, 100, 2):
    cidx = (mes-90)//2
    this_bpm = bpm_list[cidx]
    o.shift_indices(mes+offset+1, 16)
    cbpm = 1800000 + this_bpm
    o.bpm_add(mes+offset, cbpm, 0, 1)

    for i in range(4):
        o.meters[mes+i*4+offset] = 1/16
        o.meters[mes+i*4+offset+2] = 1/16
        o.stop_add(mes+offset+i*4+2, round((cbpm / this_bpm) * (192 * 7 / 32)), 0, 1)
        o.stop_add(mes+offset+i*4, round((cbpm / this_bpm) * (192 / 32)), 0, 1)

        if i == 3:
            if real_notes[cidx] is None:
                continue
            m = Measure(BDIV, 'D' + BMSparser.real_lane(real_notes[cidx]), mes + i * 4 + offset + 3)
            m.add(Note('01', 0))
            o.add(m)
            continue

        o.ignored_lines.append("#RANDOM 7\n")
        for r in range(1, 8):
            m = Measure(BDIV, 'D' + BMSparser.real_lane(r), mes+i*4+offset+4)
            m.add(Note('01', 0))
            o.ignored_lines.append("#IF %d\n" % r)
            o.ignored_lines.append(m.get_string() + '\n')
            o.ignored_lines.append("#ENDIF\n")
        o.ignored_lines.append("#ENDRANDOM\n")

    o.meters[mes + 16 + offset] = 1 / 16
    o.bpm_add(mes + 16 + offset, this_bpm, 0, 1)
    o.stop_add(mes + 16 + offset, 12, 0, 1)

    offset += 16


def velocity(i):
    return round(31 * (i / 64) ** 2)


o.shift_indices(101+1+offset, 59)
for i in range(60):
    o.meters[101+i+offset] = 1/64

for i in range(32):
    o.stop_add(101+i+offset, int((1800010 / 40) * (192 / 64)), (64-i-velocity(i)) % 64, 64)

offset += 59

o.shift_indices(102+offset, 59)
ey_mes = Measure(1, Note.LANE_BGM, 102+offset)
ey_mes.add(Note('EY', 0))
o.add(ey_mes)

for i in range(60):
    o.meters[101+i+offset] = 1/32

for i in range(32):
    o.stop_add(101+i+offset, int((1800010 / 40) * 1), (64-i-velocity(i+32)) % 64, 64)

offset += 59

# Add a random block from original
bpm_block = [60, 100, 140, 180]
lane_block = ["11", "13", "15", "19"]
for mes in range(123, 131):
    o.ignored_lines.append("#RANDOM 4\n")
    for i in range(4):
        o.ignored_lines.append("#IF %d\n" % (i+1))
        o.ignored_lines.append("#%03d%s:%s\n" % (mes+offset+1, Note.LANE_BPM , o._bpm_index(bpm_block[i])))
        o.ignored_lines.append("#%03d%s:%s\n" % (mes+offset+1, lane_block[i],
                                               "0K" if (mes - 123) % 4 == 0 else "0L"))
        o.ignored_lines.append("#ENDIF\n")
    o.ignored_lines.append("#ENDRANDOM\n")

# From something else
def show_div(mes, div, ln):
    global offset

    div //= 2
    mm = min(mes+1+offset+div, 998)
    mm -= mes + 1 + offset
    o.shift_indices(mes+1+offset, mm)
    o.stop_add(mes+offset, int((1800180 / 180) * (192 / ln)), 0, 1)
    for i in range(mm+1):
        o.meters[mes+offset+i] = 1/div/2
    offset += div

for i in range(9):
    show_div(131+i, 2**(i+1), 4)

o.shift_indices(0, 1)
o.optimize()
o.write_output("_SERA.bms")
