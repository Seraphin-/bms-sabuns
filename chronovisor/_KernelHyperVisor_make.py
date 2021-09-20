##################################################################################################################
#
# Good amount of copy pasting here.
# Ran out of time to make some of the gimmicks quite how I wanted...
#
##################################################################################################################

from gimmick import *
import random
import numpy as np
from tqdm import tqdm
from collections import defaultdict

assert BMSparser.VERSION == '1.6'
o = BMSparser("_KernelHyperVisor_base.bms")
ORIG_BPM = 200
MAX_BPM = 2000200

# 0-10
# Just a slowdown - done by hand

# 10-18
# LNs, anchors
# Appearing mine thing

conversion_targets = [1, 5, 7, 3, 2, 6, 2, 6]
for mes in range(9, 17):
    # Collect the real keysounds and remove original measures
    # We know there are 8 in 8ths, just want the note numbers
    real_ks = []
    lane = conversion_targets[mes-9]
    lane = BMSparser.real_lane(lane)
    for m in o.find((mes,), ('1' + lane,)):
        for note in m.notes:
            real_ks.append(note.object)
        o.measures.remove(m)

    valid_mes = o.find((mes,), ['*'])
    for m in valid_mes:
        # Will move notes later
        BMSparser.reindex_measure(m, 8)
        m.size *= 8
    o.meters[mes] = 8

    lane_r = Measure(128, '5' + lane, mes)
    lane_m = Measure(128, '1' + lane, mes)
    o.add(lane_r)
    o.add(lane_m)
    lane_m.add(Note(real_ks[0], 0))
    # kinda copies from below
    for i in range(1, 8):
        # Create warp at each 8th in between
        pos_s = (8 * (i - 1)) + i
        pos_e = (8 * i) + i
        o.bpm_add(mes, MAX_BPM, pos_s, 8 * 8)
        o.bpm_add(mes, ORIG_BPM, pos_e, 8 * 8)

        if i != 7:
            lane_r.add(Note(real_ks[i], pos_s*2 + i))
            lane_r.add(Note('01', (pos_s + 7)*2 - i))
        else:
            lane_m.add(Note(real_ks[i], pos_s*2 + i))

        # Move all notes at equivalent position forward 1 measure's worth
        for m in valid_mes:
            for note in m.notes:
                if note.pos >= (pos_s * m.size / 64):
                    note.pos += m.size // 8

# 18-20
# BPM display gimmick, bar line?
# This was moved to the bottom.

# 20-36
# DONE stutters on the morse sound
# DONE inverse mine display on melody?

for mes in [21, 23, 25, 27, 30, 31, 34, 92, 94, 96, 98]:
    notes_in_this = defaultdict(list)
    for m in o.find((mes,), ('11', '12', '13', '14', '15', '18', '19')):
        for note in m.notes:
            # Assume all are aligned to 8...
            notes_in_this[note.pos * 8 // m.size].append(BMSparser.lane_no(note.lane))

    valid_mes = o.find((mes,), ['*'])
    for m in valid_mes:
        # Will move notes later
        BMSparser.reindex_measure(m, 8)
        m.size *= 8

    o.meters[mes] = 8
    new_measure_storage = {}

    for i in range(1, 8):
        # Create warp at each 8th in between
        pos_s = (8 * (i - 1)) + i
        pos_e = (8 * i) + i
        o.bpm_add(mes, MAX_BPM, pos_s, 8 * 8)
        o.bpm_add(mes, ORIG_BPM, pos_e, 8 * 8)

        # Add mines +1 of pos_s
        for lane in range(1, 8):
            if lane not in notes_in_this[i]:
                if lane not in new_measure_storage:
                    new_measure_storage[lane] = Measure(64, 'D' + BMSparser.real_lane(lane), mes)
                    o.add(new_measure_storage[lane])
                new_measure_storage[lane].add(Note('02', pos_s+1))

        # Move all notes at equivalent position forward 1 measure's worth
        for m in valid_mes:
            for note in m.notes:
                if note.pos >= (pos_s * m.size / 64):
                    note.pos += m.size // 8

for m in o.find(range(28, 34), ('16',)):
    for note in m.notes:
        o.bpm_add(m.number, MAX_BPM, note.pos, m.size, overwrite=True)
        o.stop_add(m.number, int((MAX_BPM / ORIG_BPM) * (192 / 16)), note.pos, m.size)
        if note.pos + 1 < m.size:
            o.bpm_add(m.number, ORIG_BPM, note.pos+1, m.size)

# 36-52
# Manual soflan, gimmicks?
# -> Soflan is adjusted automatically...
# use 1008's 17s

# fucking ubmsc saving 03 channel along with 08
MEASURE_DIV = 672  # 672, 1736, 3472? all choices with ok factors?
soflan_ranges = {}
temp_dict = {}

for k, v in o.bpm_objects.items():
    temp_dict[v] = k

print("[@] Generating BPM effect...")

multiplier = 1
for m in tqdm(range(36, 52)):
    soflan_ranges = {}

    MEASURE_DIV_adj = int(o.meters[m] * MEASURE_DIV) if m in o.meters else MEASURE_DIV

    for mm in o.find((m,), ['03', '08']):
        if mm.lane == '03':
            for note in mm.notes:
                soflan_ranges[note.pos * MEASURE_DIV_adj // mm.size] = int(note.object, 16)
        else:
            for note in mm.notes:
                soflan_ranges[note.pos * MEASURE_DIV_adj // mm.size] = temp_dict[note.object]
        o.measures.remove(mm)

    for i in range(MEASURE_DIV_adj):
        if i in soflan_ranges:
            multiplier = 200 / soflan_ranges[i]
        max_temp = MAX_BPM + random.randrange(-500, 500)
        o.bpm_add(m, max_temp, i, MEASURE_DIV_adj)
        o.stop_add(m, int((max_temp / ORIG_BPM) * (192 / MEASURE_DIV) * multiplier), i, MEASURE_DIV_adj)

o.bpm_add(52, ORIG_BPM, 0, 1)

# 52-68
# nothing here now

# 68-71
# Some art, done by hand

# slow on beat
# apply the slowdown right before a 0H and end

for m in o.find(range(71, 87), ['*']):
    BMSparser.reindex_measure(m, 256)
for mes in range(71, 87):
    m_ref = o.find((mes,), ('11',))[0]
    if mes not in o.meters:
        o.meters[mes] = 1
    running_delta = 0
    for note in m_ref.notes:
        if note.pos == 0:
            continue
        o.bpm_add(mes, 100, note.pos - 16, 256 - running_delta)
        delta = 16 // 2
        running_delta += delta
        o.meters[mes] -= 1/32
        orig_pos = note.pos
        # Move all down!
        for m in o.find((mes,), ['*']):
            m.size -= delta
            for m_note in m.notes:
                if m_note.pos >= orig_pos:
                    m_note.pos -= delta
        # These too
        for m in o.bpm_measures.values():
            if m.number != mes:
                continue
            m.size -= delta
            for m_note in m.notes:
                if m_note.pos >= orig_pos:
                    m_note.pos -= delta
        o.bpm_add(mes, 200, note.pos, 256 - running_delta)
o.bpm_add(87, ORIG_BPM, 0, 1)

# 87-91
# manual soflan

# 91-End
# Some combo effects from before

for index, mes in enumerate([91, 93, 95, 97]):
    max_temp = 2000200 + index
    o.bpm_add(mes, max_temp, 0, 1)
    o.bpm_add(mes+1, ORIG_BPM, 0, 1)
    for i in range(256):
        o.stop_add(mes, int((max_temp / ORIG_BPM) * (192 / 256)), i, 256)

for mes in range(100, 102):
    for i in range(256*3//4):
        max_temp = MAX_BPM + random.randrange(-500, 500)
        o.bpm_add(mes, max_temp, i, 256*3//4)
        o.stop_add(mes, int((max_temp / ORIG_BPM) * (192 / 256)), i, 256*3//4)
o.bpm_add(102, ORIG_BPM, 0, 1)


# Now for the bar line gimmick


def inverse_g(a_p, b_p, c_p, y_p):
    inv = np.sqrt(2) * np.sqrt(c_p * c_p * np.log(a_p / y_p))
    return {b_p + inv, b_p - inv}


# Bar line gimmicks
checkpoints = [1, 3, 5, 7, 8, 9, 9.33, 9.66]
# and one at b
cur_i = 18
print("[@] Generating bar lines...")
for i in range(1, 57):
    c = 5-(1/160)*(i-28)**2
    b = c + 2.5
    measure_positions = []
    for y in checkpoints:
        for xp in inverse_g(10, b, c, y):
            if 0 < xp <= 10:
                measure_positions.append(xp / 20)
    measure_positions.append(b / 20)
    measure_positions.sort()

    # Shift everything needed amount
    o.shift_indices(cur_i+1, len(measure_positions)+1)

    max_temp = MAX_BPM + random.randrange(0, 100)
    o.bpm_add(cur_i, max_temp, 0, 1)
    o.stop_add(cur_i, int((MAX_BPM // ORIG_BPM) * 192 / 32), 0, 1)

    # Add each measure for position
    cur_p = 0
    for xp in measure_positions:
        o.meters[cur_i] = xp - cur_p
        cur_p = xp
        cur_i += 1
    # Add the remaining padding
    o.meters[cur_i] = 1 - cur_p
    cur_i += 1

cur_i += 1
print("[@] Finishing up!")
o.shift_indices(cur_i+1, 99)
for i in range(100):
    o.meters[cur_i + i] = 1/100/8

randomize(o, 956, 964, 8)

o.bpm_add(cur_i+1, ORIG_BPM, 0, 1)
o.optimize()
o.write_output("_KernelHyperVisor_output.bms")
