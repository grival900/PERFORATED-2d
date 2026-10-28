"""Synthesises the Level 1 music loop (dark, pulsing, A minor, 120 BPM, 32 s).

Run:  python3 2D-lab/game/tools/gen_music.py      (needs numpy)
Output: game/assets/music/pride_loop.wav  (22.05 kHz, mono, 16-bit, seamless loop)
All sounds are generated here from oscillators; nothing is sampled or copied.
"""
import wave
from pathlib import Path

import numpy as np

SR = 22050
BPM = 120
BEAT = 60.0 / BPM
BARS = 16
OUT = Path(__file__).resolve().parent.parent / "assets" / "music" / "pride_loop.wav"
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lowpass(x, cutoff):
    """One-pole low-pass."""
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):          # fine at this size, offline tool
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * freq * (1 + detune)) % 1.0) - 1


def env(n, attack, release, curve=2.0):
    e = np.ones(n)
    a = max(1, int(attack * SR))
    r = max(1, int(release * SR))
    e[:a] = np.linspace(0, 1, a) ** curve
    e[-r:] *= np.linspace(1, 0, r) ** curve
    return e


def add(buf, start, sig):
    i = int(start * SR)
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def main():
    total = int(BARS * 4 * BEAT * SR)
    bass = np.zeros(total)
    pad = np.zeros(total)
    arp = np.zeros(total)
    drums = np.zeros(total)

    # chord roots per bar (A minor loop): Am F C G
    roots = [45, 41, 48, 43]           # A2 F2 C3 G2
    chords = [(57, 60, 64), (53, 57, 60), (60, 64, 67), (55, 59, 62)]

    for bar in range(BARS):
        r = roots[bar % 4]
        ch = chords[bar % 4]
        t0 = bar * 4 * BEAT
        # pulsing bass on eighth notes
        for k in range(8):
            n = int(BEAT * 0.5 * SR * 0.9)
            f = midi(r - 12 if k % 4 == 3 else r - 12)
            sig = lowpass(saw(f, n) + 0.6 * saw(f, n, 0.004), 380) * env(n, 0.004, 0.08)
            add(bass, t0 + k * BEAT * 0.5, sig * (0.55 if k % 2 == 0 else 0.4))
        # pad: detuned saw chord, slow attack
        n = int(4 * BEAT * SR)
        p = np.zeros(n)
        for note in ch:
            f = midi(note)
            p += saw(f, n, -0.003) + saw(f, n, 0.003)
        p = lowpass(p, 900) * env(n, 0.9, 1.0, 1.5) * 0.10
        add(pad, t0, p)
        # arpeggio: bell-ish notes on sixteenths with a rest pattern
        pattern = [0, 2, 1, 2, 0, 1, 2, 1, 0, 2, 1, 2, 2, 1, 0, 1]
        for k, idx in enumerate(pattern):
            if (bar % 4 == 3) and k >= 12:
                continue
            note = ch[idx] + 12
            n = int(BEAT * 1.4 * SR)
            t = np.arange(n) / SR
            f = midi(note)
            sig = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.01 * t) +
                   0.25 * np.sin(2 * np.pi * f * 3.97 * t)) * np.exp(-t * 4.2)
            add(arp, t0 + k * BEAT * 0.25, sig * 0.10)
        # drums: soft kick on beats, closed hat on offbeats, snare-ish noise on 2/4
        for beat in range(4):
            tb = t0 + beat * BEAT
            n = int(0.22 * SR)
            t = np.arange(n) / SR
            kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-t * 28)) * t) * np.exp(-t * 14)
            add(drums, tb, kick * 0.6)
            if beat % 2 == 1:
                n2 = int(0.16 * SR)
                noise = rng.standard_normal(n2) * np.exp(-np.arange(n2) / SR * 24)
                add(drums, tb, lowpass(noise, 3500) * 0.28)
            n3 = int(0.04 * SR)
            hat = rng.standard_normal(n3) * np.exp(-np.arange(n3) / SR * 90)
            add(drums, tb + BEAT * 0.5, (hat - lowpass(hat, 4000)) * 0.12)

    mix = bass + pad + arp + drums
    # feedback delay for space
    d = int(BEAT * 0.75 * SR)
    wet = mix.copy()
    for k in range(1, 5):
        wet[d * k:] += mix[: len(mix) - d * k] * (0.35 ** k) * 0.7
    # make the loop seamless: wrap the tail of the delay onto the start
    tail = wet[total:] if len(wet) > total else np.zeros(0)
    mix = wet[:total]
    mix = np.tanh(mix * 1.1)
    mix /= np.max(np.abs(mix)) / 0.8
    fade = int(0.01 * SR)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix[-fade:] *= np.linspace(1, 0, fade)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("saved", OUT, f"{len(pcm) / SR:.1f}s")


if __name__ == "__main__":
    main()
