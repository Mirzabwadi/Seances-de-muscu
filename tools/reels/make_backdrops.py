"""Generate original 1188x2112 vertical backdrops for a Reel: starfield, sea, sky, light.

No licence to credit: these are drawn here, not downloaded. The palette matches the
series (deep brown-black ground, gold accent) so they sit next to the paintings.

Usage: python3 make_backdrops.py OUT_DIR [name ...]     (default: all)
Names: ciel, mer, pierre, lumiere, poussiere, causes, paysage, tempete
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H = 1188, 2112
rng = np.random.default_rng(20261117)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
nx, ny = xx / W, yy / H


def save(name, rgb, out_dir):
    """rgb: float array (H, W, 3) in 0..1."""
    path = Path(out_dir) / f"bg-{name}.jpg"
    data = (np.clip(rgb, 0, 1) * 255).astype(np.uint8).tobytes()
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-i", "-", "-q:v", "3", str(path)],
        input=data, check=True)
    print(path)


def smooth(shape, scale, seed):
    """Value noise: random grid, bilinearly zoomed to `shape`."""
    r = np.random.default_rng(seed)
    h, w = max(2, int(shape[0] / scale)), max(2, int(shape[1] / scale))
    g = r.random((h, w)).astype(np.float32)
    iy = np.linspace(0, h - 1, shape[0])
    ix = np.linspace(0, w - 1, shape[1])
    y0, x0 = np.floor(iy).astype(int), np.floor(ix).astype(int)
    y1, x1 = np.minimum(y0 + 1, h - 1), np.minimum(x0 + 1, w - 1)
    fy, fx = (iy - y0)[:, None], (ix - x0)[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    top = g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx
    bot = g[y1][:, x0] * (1 - fx) + g[y1][:, x1] * fx
    return top * (1 - fy) + bot * fy


def fractal(seed, octaves=5, base=240.0):
    out, amp, total = 0.0, 1.0, 0.0
    for o in range(octaves):
        out = out + amp * smooth((H, W), base / (2 ** o), seed + o)
        total += amp
        amp *= 0.55
    return out / total


def ciel():
    """Night sky: nebula haze, star field, a few bright gold stars."""
    neb = fractal(1, 6, 420)
    base = np.stack([
        0.05 + 0.20 * neb ** 2.2 + 0.05 * (1 - ny),
        0.06 + 0.17 * neb ** 2.2 + 0.06 * (1 - ny),
        0.11 + 0.22 * neb ** 2.0 + 0.10 * (1 - ny),
    ], -1)
    stars = np.zeros((H, W), np.float32)
    n = 1800
    sy = rng.integers(0, H, n)
    sx = rng.integers(0, W, n)
    mag = 0.35 + 1.5 * rng.random(n) ** 2.2
    np.add.at(stars, (sy, sx), mag)
    # bloom: three box blurs of growing radius
    glow = stars.copy()
    for k in (3, 9, 25):
        ker = np.ones(k, np.float32) / k
        glow = np.apply_along_axis(lambda m: np.convolve(m, ker, "same"), 1, glow)
        glow = np.apply_along_axis(lambda m: np.convolve(m, ker, "same"), 0, glow)
        stars = stars + glow * 0.9
    s = np.clip(stars, 0, 1)[..., None]
    gold = np.array([1.0, 0.92, 0.72], np.float32)
    return base + s * gold


def mer():
    """Dark sea: crests crowding towards the horizon, one low gold light across them."""
    horizon = 0.30
    depth = np.clip((ny - horizon) / (1 - horizon), 0, 1)
    # Perspective: crests pack together as they approach the horizon.
    phase = 5.5 / (0.07 + depth) + 0.9 * smooth((H, W), 300, 21)
    crest = (0.5 + 0.5 * np.sin(2 * np.pi * phase)) ** 7
    crest *= np.clip(depth * 5, 0, 1)
    water = np.stack([
        0.05 + 0.09 * depth,
        0.07 + 0.11 * depth,
        0.10 + 0.13 * depth,
    ], -1)
    sky_t = np.clip(ny / horizon, 0, 1)
    sky = np.stack([
        0.30 - 0.12 * sky_t,
        0.24 - 0.10 * sky_t,
        0.18 - 0.07 * sky_t,
    ], -1)
    mask = np.clip((ny - horizon) * 40, 0, 1)[..., None]
    gold = np.array([1.0, 0.86, 0.55], np.float32)
    beam = np.exp(-(((nx - 0.5) / 0.26) ** 2)).astype(np.float32)
    return sky * (1 - mask) + water * mask + (crest * beam * 0.85)[..., None] * gold


def pierre():
    """A stone's arc across an open sky: the image Spinoza uses for false freedom."""
    sky = np.stack([
        0.08 + 0.30 * (1 - ny) ** 1.6,
        0.09 + 0.26 * (1 - ny) ** 1.6,
        0.12 + 0.22 * (1 - ny) ** 1.4,
    ], -1)
    cloud = fractal(3, 5, 300)
    sky += (np.clip(cloud - 0.45, 0, 1) * 0.55)[..., None] * np.array([0.9, 0.82, 0.7], np.float32) * (1 - ny)[..., None]
    # Parabola from bottom-left to bottom-right, apex high.
    t = nx
    arc = 0.26 + 2.6 * (t - 0.5) ** 2
    d = np.abs(ny - arc)
    trail = np.exp(-((d / 0.006) ** 2)) * np.clip(1 - 2.1 * np.abs(t - 0.5), 0, 1)
    stone_t, stone_y = 0.62, 0.26 + 2.6 * (0.62 - 0.5) ** 2
    sd = np.sqrt(((nx - stone_t) * W) ** 2 + ((ny - stone_y) * H) ** 2)
    stone = np.exp(-((sd / 13.0) ** 2)) + 0.45 * np.exp(-((sd / 40.0) ** 2))
    gold = np.array([1.0, 0.86, 0.5], np.float32)
    return sky + (trail * 0.55 + stone)[..., None] * gold


def lumiere():
    """Light opening out of darkness: understanding as joy. Soft, not a sunburst."""
    cx, cy = 0.5, 0.40
    d = np.sqrt(((nx - cx) * 1.0) ** 2 + ((ny - cy) * 0.62) ** 2)
    core = 0.42 * np.exp(-((d / 0.15) ** 2)) + 0.34 * np.exp(-((d / 0.40) ** 2))
    ang = np.arctan2(ny - cy, nx - cx)
    rays = (0.5 + 0.5 * np.sin(ang * 9 + 0.6)) ** 2 * np.exp(-((d / 0.52) ** 2)) * 0.05
    haze = fractal(5, 4, 260) * 0.10
    gold = np.array([1.0, 0.88, 0.62], np.float32)
    warm = np.array([0.55, 0.40, 0.24], np.float32)
    base = np.stack([0.05 + 0.03 * (1 - ny), 0.045 + 0.025 * (1 - ny), np.full_like(ny, 0.04)], -1)
    return base + core[..., None] * gold + (rays + haze)[..., None] * warm


def poussiere():
    """Quiet dark texture: a fallback backdrop that never competes with the text."""
    grain = fractal(9, 6, 160)
    motes = np.zeros((H, W), np.float32)
    n = 420
    np.add.at(motes, (rng.integers(0, H, n), rng.integers(0, W, n)), rng.random(n) ** 2)
    ker = np.ones(7, np.float32) / 7
    for _ in range(3):
        motes = np.apply_along_axis(lambda m: np.convolve(m, ker, "same"), 1, motes)
        motes = np.apply_along_axis(lambda m: np.convolve(m, ker, "same"), 0, motes)
    base = np.stack([
        0.07 + 0.10 * grain + 0.05 * (1 - ny),
        0.06 + 0.08 * grain + 0.04 * (1 - ny),
        0.05 + 0.06 * grain + 0.03 * (1 - ny),
    ], -1)
    return base + (motes * 7)[..., None] * np.array([1.0, 0.9, 0.7], np.float32)


def causes():
    """A lattice of linked points receding without end: every cause has a cause."""
    img = np.zeros((H, W), np.float32)
    r = np.random.default_rng(31)
    layers = 7
    for L in range(layers):
        depth = L / (layers - 1)          # 0 near, 1 far
        count = 5 + 3 * L
        y0 = 0.14 + 0.72 * (1 - depth) ** 1.25
        spread = 0.46 * (1 - 0.65 * depth)
        px = 0.5 + (np.linspace(-1, 1, count) + r.normal(0, 0.06, count)) * spread
        py = y0 + r.normal(0, 0.012, count)
        size = 9.0 * (1 - 0.72 * depth)
        bright = 1.0 - 0.72 * depth
        if L:
            for a in range(count):
                for b in (a - 1, a, a + 1):
                    if 0 <= b < len(prev_x):
                        x1, y1, x2, y2 = px[a] * W, py[a] * H, prev_x[b] * W, prev_y[b] * H
                        t = np.linspace(0, 1, 160)
                        for tx, ty in zip(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t):
                            yi, xi = int(ty), int(tx)
                            if 0 <= yi < H and 0 <= xi < W:
                                img[yi, xi] = max(img[yi, xi], 0.5 * bright)
        for a in range(count):
            d = np.sqrt((xx - px[a] * W) ** 2 + (yy - py[a] * H) ** 2)
            img += bright * np.exp(-((d / size) ** 2))
        prev_x, prev_y = px, py
    ker = np.ones(5, np.float32) / 5
    glow = img.copy()
    for _ in range(2):
        glow = np.apply_along_axis(lambda m: np.convolve(m, ker, "same"), 1, glow)
        glow = np.apply_along_axis(lambda m: np.convolve(m, ker, "same"), 0, glow)
    img = np.clip(img + glow * 0.8, 0, 1.4)
    base = np.stack([0.06 + 0.05 * (1 - ny), 0.055 + 0.04 * (1 - ny), 0.07 + 0.05 * (1 - ny)], -1)
    gold = np.array([1.0, 0.87, 0.58], np.float32)
    return base + img[..., None] * gold * 0.72


def paysage():
    """An open country at dusk: man as one part of the whole of Nature."""
    sky_t = np.clip(ny / 0.62, 0, 1)
    img = np.stack([
        0.40 - 0.30 * sky_t,
        0.30 - 0.23 * sky_t,
        0.22 - 0.15 * sky_t,
    ], -1)
    sun_d = np.sqrt(((nx - 0.56) * 1.0) ** 2 + ((ny - 0.54) * 1.7) ** 2)
    img += (0.55 * np.exp(-((sun_d / 0.10) ** 2)))[..., None] * np.array([1.0, 0.84, 0.52], np.float32)
    cloud = fractal(13, 4, 320)
    band = np.exp(-(((ny - 0.34) / 0.14) ** 2))
    img += (np.clip(cloud - 0.5, 0, 1) * band * 0.7)[..., None] * np.array([1.0, 0.76, 0.5], np.float32)
    # Three ridges, each darker and lower than the last.
    for k, (base_y, amp, scale, dark) in enumerate(
            ((0.62, 0.035, 520, 0.42), (0.71, 0.05, 330, 0.26), (0.82, 0.07, 190, 0.12))):
        ridge = base_y + (smooth((H, W), scale, 50 + k)[0] - 0.5) * amp
        mask = (ny >= ridge[None, :])
        img = np.where(mask[..., None], np.stack([
            np.full_like(ny, dark * 0.9), np.full_like(ny, dark * 0.78), np.full_like(ny, dark * 0.62)], -1), img)
    return img


def tempete():
    """Turbulent dark sky: the passions, when they carry someone who does not understand them."""
    warp = (fractal(17, 5, 260) - 0.5) * 0.22
    swirl = fractal(19, 6, 520)
    streak = 0.5 + 0.5 * np.sin(2 * np.pi * (3.2 * (ny + warp) + 1.4 * np.sin(2 * np.pi * nx * 0.8)))
    streak = streak ** 2
    body = 0.45 * swirl + 0.55 * streak
    body = np.clip((body - 0.28) * 1.9, 0, 1)
    light = np.exp(-(((nx - 0.42) / 0.35) ** 2)) * np.exp(-(((ny - 0.28) / 0.30) ** 2))
    img = np.stack([
        0.06 + 0.52 * body * (0.45 + light),
        0.06 + 0.42 * body * (0.45 + light),
        0.07 + 0.34 * body * (0.45 + light),
    ], -1)
    img += (np.clip(body - 0.62, 0, 1) * light * 2.0)[..., None] * np.array([1.0, 0.82, 0.52], np.float32)
    return img * (0.62 + 0.38 * (1 - ny))[..., None]


MAKERS = {"ciel": ciel, "mer": mer, "pierre": pierre, "lumiere": lumiere, "poussiere": poussiere,
          "causes": causes, "paysage": paysage, "tempete": tempete}

if __name__ == "__main__":
    out_dir = sys.argv[1]
    names = sys.argv[2:] or list(MAKERS)
    for nme in names:
        save(nme, MAKERS[nme](), out_dir)
