"""Read a melody out of a MIDI file, with no dependencies.

A melody written in a DAW is easier to export than to retype, and retyping is
where transcription errors come from. This pulls the note-on events, keeps the
top note wherever chords overlap, and hands back one pitch per note so `check`
and `fit` can line it up against the syllables.
"""

import struct


def _varint(data, i):
    value = 0
    while True:
        byte = data[i]
        i += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, i


def _events(chunk):
    """(absolute tick, pitch) for every note-on in one track."""
    out = []
    i, tick, status = 0, 0, None
    while i < len(chunk):
        delta, i = _varint(chunk, i)
        tick += delta
        if i >= len(chunk):
            break
        byte = chunk[i]
        if byte == 0xFF:                        # meta event
            i += 2
            length, i = _varint(chunk, i)
            i += length
            continue
        if byte in (0xF0, 0xF7):                # sysex
            i += 1
            length, i = _varint(chunk, i)
            i += length
            continue
        if byte & 0x80:
            status = byte
            i += 1
        if status is None:
            break
        kind = status & 0xF0
        if kind in (0xC0, 0xD0):                # one data byte
            i += 1
            continue
        pitch, velocity = chunk[i], chunk[i + 1]
        i += 2
        if kind == 0x90 and velocity > 0:
            out.append((tick, pitch))
    return out


def read(path, track=None):
    """Every note in the file, in time order, as MIDI numbers.

    Notes starting on the same tick are one chord, and only its top note is
    kept, because a syllable is sung on one pitch. Pass a track index to read a
    single track when the file carries more than the melody.
    """
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:4] != b"MThd":
        raise ValueError(f"{path} is not a MIDI file")
    header = struct.unpack(">HHH", data[8:14])
    tracks, i = [], 8 + struct.unpack(">I", data[4:8])[0]
    while i < len(data) and data[i:i + 4] == b"MTrk":
        length = struct.unpack(">I", data[i + 4:i + 8])[0]
        tracks.append(data[i + 8:i + 8 + length])
        i += 8 + length
    if not tracks:
        raise ValueError(f"{path} has no tracks")

    if track is not None:
        chosen = [_events(tracks[track])]
    elif header[0] == 0:
        chosen = [_events(tracks[0])]
    else:
        # Type 1 usually puts tempo and key alone on track 0. Take whichever
        # track carries the most notes rather than guessing by position.
        parsed = [_events(t) for t in tracks]
        chosen = [max(parsed, key=len)] if any(parsed) else []

    notes = sorted({(tick, pitch) for events in chosen for tick, pitch in events})
    out = []
    for tick, pitch in notes:
        if out and out[-1][0] == tick:
            out[-1] = (tick, max(out[-1][1], pitch))
        else:
            out.append((tick, pitch))
    return [pitch for _tick, pitch in out]


def track_summary(path):
    """(index, note count) per track, for choosing one by hand."""
    with open(path, "rb") as handle:
        data = handle.read()
    out, index, i = [], 0, 8 + struct.unpack(">I", data[4:8])[0]
    while i < len(data) and data[i:i + 4] == b"MTrk":
        length = struct.unpack(">I", data[i + 4:i + 8])[0]
        out.append((index, len(_events(data[i + 8:i + 8 + length]))))
        index += 1
        i += 8 + length
    return out
