##################################################################################################################
#
# Because I refactored the chart a few times there are a lot of commented out sections.
# Each of the main blocks is mostly just copy pasted, too...
#
##################################################################################################################

from gimmick import *
import random
from collections import defaultdict
import itertools

assert BMSparser.VERSION == '1.6'

o = BMSparser('martyr_fractions_.bme')

ORIG_BPM = 155
MAX_BASE = 15500000

# 9-21 single,

# For all possibilities, create a measure...
# Each measure previews next
"""
next_choice = 0
max_bpm = 0


for mes in range(8, 21):
    # Generate next one
    next_choice_temp = next_choice

    if mes != 20:
        next_choice = random.randrange(1, 8)
        max_bpm = MAX_BASE + next_choice * 10
        # Apply BPM
        o.bpm_add(mes, max_bpm, 0, 1)
    else:
        max_bpm = MAX_BASE + 999
        o.bpm_add(mes, max_bpm, 0, 1)

    if mes == 8:
        for i in range(512):
            o.stop_add(mes, int((max_bpm / ORIG_BPM) * (192 / 512)), i, 512)
        continue

    # Pull appropriate notes into a dict in time
    note_dict = defaultdict(list)
    mes_list = {}
    for note in g.all_notes[mes]:
        note_dict[note.pos].append(note)


    # Apply the note effect.
    # We'll use standard stop fun, apply a 25 at each quarter and skip before with measure of space?
    o.meters[mes] = 8  # All are 1 for start

    note_m = Measure(4, '1' + BMSparser.real_lane(next_choice_temp), mes)
    o.add(note_m)
    # Feels like I could do this smarter but whatever
    for quarter in range(4):
        # Insert the note to be hitting...
        note_m.add(Note('25', quarter))
        for spec in range(12):
            # Create 4 short stops
            o.stop_add(mes, int((max_bpm / ORIG_BPM) * (192 / 48)), 128*quarter + spec, 512)
            # Add the rest of the notes
            for note in note_dict[quarter*12+spec]:
                if note.object == '25': continue
                note.pos = 128*quarter + spec
                temp_mes = Measure(512, note.lane, mes)
                temp_mes.add(note)
                o.add(temp_mes)
"""

next_choice = 0
max_bpm = 0

# Capture notes
g = InsertMesGimmick(o, mes_div=48)
g.run_adjusted(9, 21, ['*'])

# --- Place the static notes back...
for mes in range(9, 21):
    # Pull appropriate notes into a dict in time
    note_dict = defaultdict(list)
    mes_list = {}
    for note in g.all_notes[mes]:
        note_dict[note.pos].append(note)


    # Apply the note effect.
    # We'll use standard stop fun, apply a 25 at each quarter and skip before with measure of space?
    o.meters[mes] = 8  # All are 1 for start

    for quarter in range(4):
        for spec in range(12):
            for note in note_dict[quarter*12+spec]:
                if note.object == '25': continue
                note.pos = 128*quarter + spec
                temp_mes = Measure(512, note.lane, mes)
                temp_mes.add(note)
                o.add(temp_mes)

# --- Generate the random parts!
for mes in range(8, 20):
    o.ignored_lines.append('#RANDOM 7\n')
    for choice in range(1, 8):
        o.ignored_lines.append('#IF %d\n' % choice)
        max_bpm = MAX_BASE + choice * 10
        # Place the BPMs and stops in the current measure
        bpm_mes = Measure(1, Note.LANE_BPM, mes)
        bpm_index = o._bpm_index(max_bpm)
        bpm_mes.add(Note(bpm_index, 0))
        stop_mes = Measure(512, Note.LANE_STOP, mes)
        if mes == 8:
            for i in range(512):
                stop_index = o._stop_index(int((max_bpm / ORIG_BPM) * (192 / 512)))
                stop_mes.add(Note(stop_index, i))

        # Place the notes to play in mes+1
        note_m = Measure(4, '1' + BMSparser.real_lane(choice), mes+1)
        # Feels like I could do this smarter but whatever
        for quarter in range(4):
            # Insert the note to be hitting...
            note_m.add(Note('25', quarter))
            if mes != 8:
                for spec in range(12):
                    # Create 4 short stops
                    stop_index = o._stop_index(int((max_bpm / ORIG_BPM) * (192 / 48)))
                    stop_mes.add(Note(stop_index, 128*quarter + spec))

        # Get the measures
        o.ignored_lines.append(bpm_mes.get_string() + '\n')
        o.ignored_lines.append(stop_mes.get_string() + '\n')
        o.ignored_lines.append(note_m.get_string() + '\n')

        o.ignored_lines.append('#ENDIF\n')

max_bpm = MAX_BASE + 999
o.bpm_add(20, max_bpm, 0, 1)
for quarter in range(4):
    for spec in range(12):
        o.stop_add(20, int((max_bpm / ORIG_BPM) * (192 / 48)), 128 * quarter + spec, 512)

o.bpm_add(21, ORIG_BPM, 0, 1)


# 25-37 2 note X0X

"""
g = InsertMesGimmick(o, mes_div=32)
g.run_adjusted(25, 37, ['*'])
next_choice = (0, 0)

for mes in range(24, 37):
    # Generate next one
    next_choice_temp = next_choice

    if mes != 37:
        next_choice = tuple(random.sample(range(1, 8), 2))
        max_bpm = MAX_BASE + next_choice[0] * 100 + next_choice[1]
        # Apply BPM
        o.bpm_add(mes, max_bpm, 0, 1)
    else:
        max_bpm = MAX_BASE + 999
        o.bpm_add(mes, max_bpm, 0, 1)

    if mes == 24:
        for i in range(512):
            o.stop_add(mes, int((max_bpm / ORIG_BPM) * (192 / 512)), i, 512)
        continue

    # Pull appropriate notes into a dict in time
    note_dict = defaultdict(list)
    mes_list = {}
    for note in g.all_notes[mes]:
        note_dict[note.pos].append(note)


    # Apply the note effect.
    # We'll use standard stop fun, apply a 25 at each quarter and skip before with measure of space?
    o.meters[mes] = 8  # All are 1 for start

    # TODO dont use 26 for very first
    note_m1 = Measure(4, '1' + BMSparser.real_lane(next_choice_temp[0]), mes)
    o.add(note_m1)
    note_m2 = Measure(4, '1' + BMSparser.real_lane(next_choice_temp[1]), mes)
    o.add(note_m2)
    # Feels like I could do this smarter but whatever
    for quarter in range(4):
        # Insert the note to be hitting...
        note_m1.add(Note('25', quarter))
        note_m2.add(Note('26', quarter))

        for spec in range(8):
            # Create 4 short stops
            o.stop_add(mes, int((max_bpm / ORIG_BPM) * (192 / 32)), 128*quarter + spec, 512)
            # Add the rest of the notes
            for note in note_dict[quarter*8+spec]:
                if note.object in {'25', '26'}: continue
                note.pos = 128*quarter + spec
                temp_mes = Measure(512, note.lane, mes)
                temp_mes.add(note)
                o.add(temp_mes)

o.bpm_add(37, ORIG_BPM, 0, 1)
"""

next_choice = (0, 0)
max_bpm = 0

# Capture notes
g = InsertMesGimmick(o, mes_div=32)
g.run_adjusted(25, 37, ['*'])

# --- Place the static notes back...
for mes in range(25, 37):
    # Pull appropriate notes into a dict in time
    note_dict = defaultdict(list)
    mes_list = {}
    for note in g.all_notes[mes]:
        note_dict[note.pos].append(note)


    # Apply the note effect.
    # We'll use standard stop fun, apply a 25 at each quarter and skip before with measure of space?
    o.meters[mes] = 8  # All are 1 for start

    for quarter in range(4):
        for spec in range(8):
            for note in note_dict[quarter*8+spec]:
                if note.object == '25': continue
                if note.object == '26': continue
                if note.object == '5F': continue
                note.pos = 128*quarter + spec
                temp_mes = Measure(512, note.lane, mes)
                temp_mes.add(note)
                o.add(temp_mes)

# --- Generate the random parts!
for mes in range(24, 36):
    o.ignored_lines.append('#RANDOM 21\n') # 7 choose 2
    for index, choice in enumerate(itertools.combinations(range(1, 8), 2), 1):
        o.ignored_lines.append('#IF %d\n' % index)
        max_bpm = MAX_BASE + choice[0] * 100 + choice[1]
        # Place the BPMs and stops in the current measure
        bpm_mes = Measure(1, Note.LANE_BPM, mes)
        bpm_index = o._bpm_index(max_bpm)
        bpm_mes.add(Note(bpm_index, 0))
        stop_mes = Measure(512, Note.LANE_STOP, mes)
        if mes == 24:
            for i in range(512):
                stop_index = o._stop_index(int((max_bpm / ORIG_BPM) * (192 / 512)))
                stop_mes.add(Note(stop_index, i))

        # Place the notes to play in mes+1
        note_m1 = Measure(4, '1' + BMSparser.real_lane(choice[0]), mes+1)
        note_m2 = Measure(4, '1' + BMSparser.real_lane(choice[1]), mes+1)
        # Feels like I could do this smarter but whatever
        for quarter in range(4):
            # Insert the note to be hitting...
            note_m1.add(Note('25', quarter))
            if mes == 24 and quarter == 0:
                note_m2.add(Note('5F', quarter))
            else:
                note_m2.add(Note('26', quarter))
            if mes != 24:
                for spec in range(8):
                    # Create 4 short stops
                    stop_index = o._stop_index(int((max_bpm / ORIG_BPM) * (192 / 32)))
                    stop_mes.add(Note(stop_index, 128*quarter + spec))

        # Get the measures
        o.ignored_lines.append(bpm_mes.get_string() + '\n')
        o.ignored_lines.append(stop_mes.get_string() + '\n')
        o.ignored_lines.append(note_m1.get_string() + '\n')
        o.ignored_lines.append(note_m2.get_string() + '\n')

        o.ignored_lines.append('#ENDIF\n')

max_bpm = MAX_BASE + 999
o.bpm_add(36, max_bpm, 0, 1)
for quarter in range(4):
    for spec in range(8):
        o.stop_add(36, int((max_bpm / ORIG_BPM) * (192 / 32)), 128 * quarter + spec, 512)

# o.bpm_add(37, ORIG_BPM, 0, 1)
# Graft in the mines

mines_bms = BMSparser("martyr_fractions_37-48-mines.bme")
g.run_adjusted(37, 49, ['*'])  # eat everything here
o.shift_indices(37, 369-12)  # boom

for m in mines_bms.measures:
    if m.number == 0:
        continue
    m.number += 36
    if m.lane == '08':
        for note in m.notes:
            note.object = o._bpm_index(15500302)
    if m.lane == Note.LANE_STOP:
        for note in m.notes:
            note.object = o._stop_index(200004)
    o.add(m)

offset = 369-12

# 41-48 example?

# 49-65 2 note X/X

"""
g = InsertMesGimmick(o, mes_div=48)
g.run_adjusted(49, 64, ['*'])
next_choice = (0, 0)

fractions = [(902, 4, 5), (702, 3, 5), (502, 2, 5), (302, 1, 5), (906, 1, 5), (805, 1, 6),
             (803, 2, 6), (705, 1, 4), (703, 2, 3), (605, 1, 2), (604, 1, 5),
             (503, 1, 6), (403, 1, 3)]

for mes in range(48, 64):
    # Generate next one
    next_choice_temp = next_choice

    if mes != 64:
        next_choice = random.choice(fractions)
        max_bpm = MAX_BASE + next_choice[0]
        # Apply BPM
        o.bpm_add(mes, max_bpm, 0, 1)
    else:
        max_bpm = MAX_BASE + 999
        o.bpm_add(mes, max_bpm, 0, 1)

    if mes == 48:
        for i in range(512):
            o.stop_add(mes, int((max_bpm / ORIG_BPM) * (192 / 512)), i, 512)
        continue

    # Pull appropriate notes into a dict in time
    note_dict = defaultdict(list)
    mes_list = {}
    for note in g.all_notes[mes]:
        note_dict[note.pos].append(note)


    # Apply the note effect.
    # We'll use standard stop fun, apply a 25 at each quarter and skip before with measure of space?
    o.meters[mes] = 8  # All are 1 for start

    note_m1 = Measure(4, '1' + BMSparser.real_lane(next_choice_temp[1]), mes)
    o.add(note_m1)
    note_m2 = Measure(4, '1' + BMSparser.real_lane(next_choice_temp[2]), mes)
    o.add(note_m2)
    # Feels like I could do this smarter but whatever
    for quarter in range(4):
        # Insert the note to be hitting...
        note_m1.add(Note('25', quarter))
        note_m2.add(Note('26', quarter))

        for spec in range(12):
            # Create 4 short stops
            o.stop_add(mes, int((max_bpm / ORIG_BPM) * (192 / 48)), 128*quarter + spec, 512)
            # Add the rest of the notes
            for note in note_dict[quarter*12+spec]:
                if note.object in {'25', '26'}: continue
                note.pos = 128*quarter + spec
                temp_mes = Measure(512, note.lane, mes)
                temp_mes.add(note)
                o.add(temp_mes)

#o.bpm_add(64, ORIG_BPM, 0, 1)
"""

next_choice = (0, 0)
max_bpm = 0

# Capture notes
g = InsertMesGimmick(o, mes_div=48)
g.run_adjusted(49+offset, 64+offset, ['*'])

fractions = [(902, 4, 5), (702, 3, 5), (502, 2, 5), (302, 1, 5), (906, 1, 5), (805, 1, 6),
             (803, 2, 6), (705, 1, 4), (703, 2, 3), (605, 1, 2), (604, 1, 5),
             (503, 1, 6), (403, 1, 3)]

# --- Place the static notes back...
for mes in range(49+offset, 64+offset):
    # Pull appropriate notes into a dict in time
    note_dict = defaultdict(list)
    mes_list = {}
    for note in g.all_notes[mes]:
        note_dict[note.pos].append(note)


    # Apply the note effect.
    # We'll use standard stop fun, apply a 25 at each quarter and skip before with measure of space?
    o.meters[mes] = 8  # All are 1 for start

    for quarter in range(4):
        for spec in range(12):
            for note in note_dict[quarter*12+spec]:
                if note.object == '25': continue
                if note.object == '26': continue
                note.pos = 128*quarter + spec
                temp_mes = Measure(512, note.lane, mes)
                temp_mes.add(note)
                o.add(temp_mes)

# --- Generate the random parts!
for mes in range(48+offset, 63+offset):
    o.ignored_lines.append('#RANDOM %d\n' % len(fractions))
    for index, choice in enumerate(fractions, 1):
        o.ignored_lines.append('#IF %d\n' % index)
        max_bpm = MAX_BASE + choice[0]
        # Place the BPMs and stops in the current measure
        bpm_mes = Measure(1, Note.LANE_BPM, mes)
        bpm_index = o._bpm_index(max_bpm)
        bpm_mes.add(Note(bpm_index, 0))
        stop_mes = Measure(512, Note.LANE_STOP, mes)
        if mes == 48+offset:
            for i in range(512):
                stop_index = o._stop_index(int((max_bpm / ORIG_BPM) * (192 / 512)))
                stop_mes.add(Note(stop_index, i))

        # Place the notes to play in mes+1
        note_m1 = Measure(4, '1' + BMSparser.real_lane(choice[1]), mes+1)
        note_m2 = Measure(4, '1' + BMSparser.real_lane(choice[2]), mes+1)
        # Feels like I could do this smarter but whatever
        for quarter in range(4):
            # Insert the note to be hitting...
            note_m1.add(Note('25', quarter))
            note_m2.add(Note('26', quarter))
            if mes != 48+offset:
                for spec in range(12):
                    # Create 4 short stops
                    stop_index = o._stop_index(int((max_bpm / ORIG_BPM) * (192 / 48)))
                    stop_mes.add(Note(stop_index, 128*quarter + spec))

        # Get the measures
        o.ignored_lines.append(bpm_mes.get_string() + '\n')
        o.ignored_lines.append(stop_mes.get_string() + '\n')
        o.ignored_lines.append(note_m1.get_string() + '\n')
        o.ignored_lines.append(note_m2.get_string() + '\n')

        o.ignored_lines.append('#ENDIF\n')

max_bpm = MAX_BASE + 999
o.bpm_add(63+offset, max_bpm, 0, 1)
for quarter in range(4):
    for spec in range(12):
        o.stop_add(63+offset, int((max_bpm / ORIG_BPM) * (192 / 48)), 128 * quarter + spec, 512)

# 65- single note rolling bpm, note on 3s

"""
g = InsertMesGimmick(o, mes_div=96)
g.run_adjusted(65, 72, ['*'])
next_choice = 0
filter_v = (0, 0, 0)

for mes in range(64, 72):
    # Generate next one
    next_choice_temp = next_choice

    if mes != 71:
        next_choice = random.randrange(1, 8)
        filter_v = random.choice(((100, 1, 10), (10, 1, 100), (1, 10, 100)))

    if mes == 64:
        for i in range(512):
            max_bpm = MAX_BASE + next_choice * filter_v[0] + \
                      random.randrange(10) * filter_v[1] + random.randrange(10) * filter_v[2]
            o.bpm_add(mes, max_bpm, i, 512)
            o.stop_add(mes, int((max_bpm / ORIG_BPM) * (192 / 512)), i, 512)
        continue

    # Pull appropriate notes into a dict in time
    note_dict = defaultdict(list)
    mes_list = {}
    for note in g.all_notes[mes]:
        note_dict[note.pos].append(note)


    # Apply the note effect.
    # We'll use standard stop fun, apply a 25 at each quarter and skip before with measure of space?
    o.meters[mes] = 8  # All are 1 for start

    note_m = Measure(4, '1' + BMSparser.real_lane(next_choice_temp), mes)
    o.add(note_m)
    # Feels like I could do this smarter but whatever
    for quarter in range(4):
        # Insert the note to be hitting...
        note_m.add(Note('26', quarter))

        for spec in range(24):
            # Create a BPM
            if mes == 71:
                max_bpm = MAX_BASE + random.randrange(1000)
            else:
                max_bpm = MAX_BASE + next_choice * filter_v[0] + \
                          random.randrange(10) * filter_v[1] + random.randrange(10) * filter_v[2]
            o.bpm_add(mes, max_bpm, 128*quarter+spec, 512)
            # Create 4 short stops
            o.stop_add(mes, int((max_bpm / ORIG_BPM) * (192 / 96)), 128*quarter + spec, 512)
            # Add the rest of the notes
            for note in note_dict[quarter*24+spec]:
                if note.object in {'25', '26'}: continue
                note.pos = 128*quarter + spec
                temp_mes = Measure(512, note.lane, mes)
                temp_mes.add(note)
                o.add(temp_mes)

o.bpm_add(72, ORIG_BPM, 0, 1)
"""

# Capture notes
g = InsertMesGimmick(o, mes_div=96)
g.run_adjusted(65+offset, 72+offset, ['*'])

# --- Place the static notes back...
for mes in range(65+offset, 72+offset):
    # Pull appropriate notes into a dict in time
    note_dict = defaultdict(list)
    mes_list = {}
    for note in g.all_notes[mes]:
        note_dict[note.pos].append(note)


    # Apply the note effect.
    # We'll use standard stop fun, apply a 25 at each quarter and skip before with measure of space?
    o.meters[mes] = 8  # All are 1 for start

    for quarter in range(4):
        for spec in range(24):
            for note in note_dict[quarter*24+spec]:
                if note.object == '25': continue
                if note.object == '26': continue
                note.pos = 128*quarter + spec
                temp_mes = Measure(512, note.lane, mes)
                temp_mes.add(note)
                o.add(temp_mes)

# --- Generate the random parts!
for mes in range(64+offset, 71+offset):
    o.ignored_lines.append('#RANDOM 21\n') # 7 * 3
    for index, cf in enumerate(itertools.product(range(1, 8), ((100, 1, 10), (10, 1, 100), (1, 10, 100))), 1):
        choice, filter_v = cf
        o.ignored_lines.append('#IF %d\n' % index)

        # Place the BPMs and stops in the current measure
        bpm_mes = Measure(512, Note.LANE_BPM, mes)
        stop_mes = Measure(512, Note.LANE_STOP, mes)
        if mes == 64+offset:
            for i in range(512):
                stop_index = o._stop_index(int((max_bpm / ORIG_BPM) * (192 / 512)))
                stop_mes.add(Note(stop_index, i))
                max_bpm = MAX_BASE + choice * filter_v[0] + \
                          random.randrange(10) * filter_v[1] + random.randrange(10) * filter_v[2]
                bpm_index = o._bpm_index(max_bpm)
                bpm_mes.add(Note(bpm_index, i))

        # Place the notes to play in mes+1
        note_m = Measure(4, '1' + BMSparser.real_lane(choice), mes+1)
        # Feels like I could do this smarter but whatever
        for quarter in range(4):
            # Insert the note to be hitting...
            note_m.add(Note('26', quarter))
            if mes != 64+offset:    
                for spec in range(24):
                    max_bpm = MAX_BASE + choice * filter_v[0] + \
                              random.randrange(10) * filter_v[1] + random.randrange(10) * filter_v[2]
                    bpm_index = o._bpm_index(max_bpm)
                    bpm_mes.add(Note(bpm_index, 128 * quarter + spec))

                    # Create 4 short stops
                    stop_index = o._stop_index(int((max_bpm / ORIG_BPM) * (192 / 96)))
                    stop_mes.add(Note(stop_index, 128*quarter + spec))

        # Get the measures
        o.ignored_lines.append(bpm_mes.get_string() + '\n')
        o.ignored_lines.append(stop_mes.get_string() + '\n')
        o.ignored_lines.append(note_m.get_string() + '\n')

        o.ignored_lines.append('#ENDIF\n')

for quarter in range(4):
    for spec in range(24):
        max_bpm = MAX_BASE + random.randrange(1000)
        o.bpm_add(71+offset, max_bpm, 128*quarter + spec, 512)
        o.stop_add(71+offset, int((max_bpm / ORIG_BPM) * (192 / 96)), 128 * quarter + spec, 512)

o.bpm_add(72+offset, ORIG_BPM, 0, 1)

"""
for m in mines_bms.stop_measures.values():
    m.number += 36
    # Reindex
    for note in m.notes:
        
    o.stop_measures[m.number] = m
for m in mines_bms.bpm_measures.values():
    if m.number == 0:
        continue
    m.number += 36
    o.bpm_measures[m.number] = m
"""
o.meters[361+36] = 0.25

o.optimize()
o.write_output('martyr_fractions.bme')
