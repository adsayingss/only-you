"""A full-screen, illustrated romantic story game made with Pygame."""
from __future__ import annotations

import math
import random
import struct
import time
import wave
from dataclasses import dataclass
from pathlib import Path

import pygame
import pygame.gfxdraw

# ── Personalize the story ────────────────────────────────────────────────────
BOY_NAME = "Your Name"
GIRL_NAME = "Her Name"
PROPOSAL_MESSAGE = "Will You Be Mine Forever?"
MUSIC_FILE = "romantic_music.mp3"

WIDTH, HEIGHT, FPS = 1280, 720, 60
ROOT = Path(__file__).resolve().parent
MUSIC_PATH = ROOT / MUSIC_FILE
# Use a provided soundtrack in the project directory when its name differs
# from the configured default, instead of silently falling back to the score.
if not MUSIC_PATH.is_file():
    MUSIC_PATH = next((path for path in ROOT.glob("*.mp3") if path.is_file()), MUSIC_PATH)
FALLBACK_MUSIC = ROOT / "assets" / "moonlit_score.wav"

INK = (12, 13, 31)
CREAM = (255, 241, 229)
ROSE = (255, 157, 191)
GOLD = (255, 218, 151)


@dataclass(frozen=True)
class Beat:
    key: str
    duration: float
    caption: str = ""


STORY = [
    Beat("dark", 2.2),
    Beat("found_1", 2.8, "Some stories are written..."),
    Beat("found_2", 2.7, "Some are found..."),
    Beat("found_3", 2.1, "And some..."),
    Beat("found_4", 3.0, "just happen."),
    Beat("city", 5.0),
    Beat("notice", 4.3, "And then...\nhe saw her."),
    Beat("spellbound", 4.5, "And suddenly...\nnothing else mattered."),
    Beat("montage_walk", 3.7, f"{GIRL_NAME} became his favorite thought."),
    Beat("montage_moon", 3.7, "His eyes searched for her in every crowd."),
    Beat("montage_gaze", 3.7, "Every ordinary moment became special."),
    Beat("montage_petals", 3.7, "Somehow...\nshe became home."),
    Beat("montage_fireworks", 4.3, "With her, even the night felt brighter."),
    Beat("heart_effect", 7.8, "My heart already knew the answer.\nIt was always you."),
    Beat("walk_together", 7.5),
    Beat("life_1", 2.8, "I don't need a perfect life."),
    Beat("life_2", 3.6, "I just want a life...\nwith you."),
    Beat("stop", 1.5),
    Beat("breath", 1.8),
    Beat("reach", 2.1),
    Beat("kneel", 3.4),
    Beat("question_intro", 3.0, "There's only one question left..."),
    Beat("proposal", 8.0, f"{PROPOSAL_MESSAGE}"),
    Beat("choices", 15.0),
    Beat("accept", 7.4, "You just made him the happiest person alive."),
    Beat("forever", 8.0, "I Love You Forever"),
]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def ease(value: float) -> float:
    value = clamp(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def mix(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def heart_points(x: float, y: float, size: float) -> list[tuple[int, int]]:
    return [(round(x + math.sin(t) ** 3 * size), round(y - (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) * size / 16)) for t in (i * math.tau / 48 for i in range(49))]


def glow(surface: pygame.Surface, x: float, y: float, radius: int, color: tuple[int, int, int], strength: int = 100) -> None:
    radius = max(2, int(radius))
    layer = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    for scale in (1.0, .76, .53, .31):
        r = max(1, int(radius * scale))
        alpha = int(strength * (1.0 - scale * .68))
        pygame.draw.circle(layer, (*color, alpha), (radius * 2, radius * 2), r)
    surface.blit(layer, (round(x - radius * 2), round(y - radius * 2)), special_flags=pygame.BLEND_RGBA_ADD)


def draw_heart(surface: pygame.Surface, x: float, y: float, size: float, color: tuple[int, int, int], alpha: int = 255, halo: bool = False) -> None:
    if halo:
        glow(surface, x, y, int(size * 1.6), color, 85)
    points = heart_points(x, y, size)
    if alpha >= 255:
        pygame.gfxdraw.filled_polygon(surface, points, color)
        pygame.gfxdraw.aapolygon(surface, points, color)
    else:
        layer = pygame.Surface((int(size*2.5)+4, int(size*2.5)+4), pygame.SRCALPHA)
        local = heart_points(size*1.25+2, size*1.25+2, size)
        pygame.gfxdraw.filled_polygon(layer, local, (*color, alpha))
        pygame.gfxdraw.aapolygon(layer, local, (*color, alpha))
        surface.blit(layer, (round(x-size*1.25-2), round(y-size*1.25-2)))


class Particle:
    def __init__(self, rng: random.Random, x: float, y: float, kind: str, burst: bool = False) -> None:
        self.x, self.y, self.kind = x, y, kind
        self.life = 0.0
        self.max_life = rng.uniform(1.6, 3.5) if burst else rng.uniform(5.5, 11.0)
        self.size = rng.uniform(2.0, 8.0) if kind == "heart" else rng.uniform(2.0, 5.5)
        angle = rng.uniform(0, math.tau)
        speed = rng.uniform(75, 340) if burst else rng.uniform(10, 38)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed - (70 if kind == "petal" else 0)
        self.spin = rng.uniform(-4.0, 4.0)
        self.rotation = rng.uniform(0, math.tau)
        self.burst = burst

    def update(self, dt: float) -> None:
        self.life += dt
        self.x += self.vx * dt + math.sin(self.life * 2.6 + self.rotation) * 9 * dt
        self.y += self.vy * dt
        if not self.burst:
            self.vy -= 3.5 * dt
        else:
            self.vy += 42 * dt
            self.vx *= .994
        self.rotation += self.spin * dt

    @property
    def alive(self) -> bool:
        return self.life < self.max_life

    def draw(self, surface: pygame.Surface) -> None:
        alpha = int(255 * clamp(1 - self.life / self.max_life, 0, 1))
        if self.kind == "heart":
            draw_heart(surface, self.x, self.y, self.size, (255, 130, 177), alpha)
        elif self.kind == "petal":
            color = (247, 128, 166, alpha)
            petal = pygame.Surface((18, 11), pygame.SRCALPHA)
            pygame.draw.ellipse(petal, color, (0, 0, 18, 11))
            rotated = pygame.transform.rotate(petal, math.degrees(self.rotation))
            surface.blit(rotated, rotated.get_rect(center=(round(self.x), round(self.y))))
        else:
            color = (255, 222, 166)
            pygame.draw.circle(surface, color, (round(self.x), round(self.y)), max(1, round(self.size*.5)))


class ProposalGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("A Little Story — A Romantic Proposal")
        self.fullscreen = True
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED | pygame.DOUBLEBUF, vsync=1)
        self.clock = pygame.time.Clock()
        self.rng = random.Random(19)
        self.scene = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.font_cache: dict[tuple[str, int, bool], pygame.font.Font] = {}
        self.elapsed = 0.0
        self.beat_index = 0
        self.beat_elapsed = 0.0
        self.running = True
        self.music_volume = .72
        self.music_level = 0.0
        self.music_target = 0.0
        self.answer: str | None = None
        self.final_reached = False
        self.choice_hotspots: list[tuple[pygame.Rect, str]] = []
        self.camera_zoom = 1.0
        self.scene_dim = 0.0
        self.heart_particles: list[Particle] = []
        self.ambient = [Particle(self.rng, self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), "sparkle") for _ in range(48)]
        self.petals = [Particle(self.rng, self.rng.uniform(0, WIDTH), self.rng.uniform(0, HEIGHT), "petal") for _ in range(26)]
        self.fireworks: list[dict[str, float | int]] = []
        self.stars = [(self.rng.randrange(WIDTH), self.rng.randrange(20, 530), self.rng.uniform(.6, 2.0), self.rng.uniform(0, 7)) for _ in range(180)]
        self.clouds = [(self.rng.randrange(-100, WIDTH), self.rng.randrange(45, 290), self.rng.uniform(22, 57), self.rng.uniform(4, 14), self.rng.uniform(0, 2)) for _ in range(9)]
        self.build_backdrop()
        self.music_available = self.start_music()
        if self.music_available:
            pygame.mixer.music.set_volume(0.0)
        self.music_notice = not MUSIC_PATH.is_file()
        self.music_notice_elapsed = 0.0
        self.update_music()

    def font(self, size: int, bold: bool = False, family: str = "georgia") -> pygame.font.Font:
        key = (family, size, bold)
        if key not in self.font_cache:
            self.font_cache[key] = pygame.font.SysFont(family, size, bold=bold)
        return self.font_cache[key]

    def build_backdrop(self) -> None:
        self.gradient = pygame.Surface((WIDTH, HEIGHT)).convert()
        top, horizon = (8, 10, 32), (62, 39, 72)
        for y in range(HEIGHT):
            t = y / HEIGHT
            color = mix(top, horizon, ease(t * .84))
            pygame.draw.line(self.gradient, color, (0, y), (WIDTH, y))
        glow(self.gradient, 990, 260, 190, (103, 79, 145), 52)
        glow(self.gradient, 280, 520, 260, (108, 52, 93), 30)
        self.skyline = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        rng = random.Random(73)
        x = -10
        while x < WIDTH + 20:
            bw, bh = rng.randrange(34, 96), rng.randrange(80, 222)
            pygame.draw.rect(self.skyline, (15, 20, 42, 255), (x, 556 - bh, bw, bh))
            for wy in range(565 - bh, 554, 15):
                for wx in range(x + 7, x + bw - 5, 13):
                    if rng.random() < .28:
                        pygame.draw.rect(self.skyline, (240, 177, 136, rng.randrange(75, 170)), (wx, wy, 3, 5))
            x += bw + rng.randrange(3, 12)

    def make_fallback_score(self) -> None:
        FALLBACK_MUSIC.parent.mkdir(parents=True, exist_ok=True)
        sample_rate, duration = 22050, 18
        chords = [(146.83, 174.61, 220.00), (110.00, 146.83, 196.00), (130.81, 164.81, 196.00), (98.00, 130.81, 164.81)]
        frames = bytearray()
        for i in range(sample_rate * duration):
            t = i / sample_rate
            chord = chords[int(t // 4.5) % len(chords)]
            beat = t % 4.5
            envelope = min(1.0, beat / .6, (4.5-beat) / .7)
            notes = sum(math.sin(math.tau * frequency * t) for frequency in chord) / 3
            melody = .16 * math.sin(math.tau * chord[2] * 2 * t)
            sample = int((notes * .065 + melody * .05) * clamp(envelope, 0, 1) * 32767)
            frames.extend(struct.pack("<hh", sample, sample))
        with wave.open(str(FALLBACK_MUSIC), "wb") as stream:
            stream.setnchannels(2)
            stream.setsampwidth(2)
            stream.setframerate(sample_rate)
            stream.writeframes(frames)

    def start_music(self) -> bool:
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            if MUSIC_PATH.is_file():
                pygame.mixer.music.load(str(MUSIC_PATH))
            else:
                self.make_fallback_score()
                pygame.mixer.music.load(str(FALLBACK_MUSIC))
            pygame.mixer.music.set_volume(0.0)
            pygame.mixer.music.play(-1, fade_ms=1200)
            return True
        except (pygame.error, OSError) as error:
            self.audio_error = str(error)
            return False

    @property
    def beat(self) -> Beat:
        return STORY[self.beat_index]

    def update_music(self) -> None:
        if not self.music_available:
            return
        key = self.beat.key
        volume = .04 if key.startswith("found") or key == "dark" else .11 if key in {"stop", "breath", "question_intro", "proposal"} else .68 if key in {"accept", "forever"} else .4
        if key == "choices":
            volume = .22
        if key == "kneel":
            volume = .32
        self.music_target = volume * self.music_volume

    def next_beat(self) -> None:
        if self.beat_index < len(STORY) - 1:
            self.beat_index += 1
            self.beat_elapsed = 0.0
            self.update_music()
            if self.beat.key == "montage_fireworks":
                self.launch_firework(205, 280)
                self.launch_firework(1080, 260)
            if self.beat.key == "accept":
                self.burst(800, 375, 190)
                for x in (250, 1020):
                    self.launch_firework(x, 180)
        elif self.answer and self.beat.key == "forever":
            self.beat_elapsed = 0.0
            self.answer = None

    def burst(self, x: float, y: float, count: int = 100) -> None:
        for _ in range(count):
            kind = self.rng.choices(("heart", "petal", "sparkle"), (5, 3, 4))[0]
            self.heart_particles.append(Particle(self.rng, x, y, kind, burst=True))

    def launch_firework(self, x: float | None = None, y: float | None = None) -> None:
        x = self.rng.uniform(170, WIDTH-170) if x is None else x
        y = self.rng.uniform(95, 310) if y is None else y
        self.fireworks.append({"x": x, "y": y, "timer": 0.0, "life": 1.5, "color": self.rng.choice((0, 1, 2, 3))})

    def update_particles(self, dt: float) -> None:
        for particle in self.ambient:
            particle.update(dt)
            if particle.y < 0:
                particle.y = HEIGHT + 5
                particle.x = self.rng.randrange(WIDTH)
        self.heart_particles = [p for p in self.heart_particles if p.alive]
        for particle in self.heart_particles:
            particle.update(dt)
        if self.beat.key in {"montage_petals", "walk_together", "kneel", "question_intro", "proposal", "choices", "accept", "forever"} and len(self.petals) < 120:
            for _ in range(2 if self.beat.key in {"choices", "accept", "forever"} else 1):
                self.petals.append(Particle(self.rng, self.rng.uniform(30, WIDTH-30), -8, "petal"))
        self.petals = [p for p in self.petals if p.alive and p.y < HEIGHT+30]
        for particle in self.petals:
            particle.update(dt)
        for firework in self.fireworks[:]:
            firework["timer"] = float(firework["timer"]) + dt
            if float(firework["timer"]) >= float(firework["life"]):
                self.burst(float(firework["x"]), float(firework["y"]), 70)
                self.fireworks.remove(firework)
        if self.beat.key in {"montage_fireworks", "choices", "accept", "forever"} and self.rng.random() < .025:
            self.launch_firework()

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.beat_elapsed += dt
        self.music_notice_elapsed += dt
        if self.music_available:
            self.music_level += (self.music_target-self.music_level)*min(1.0, dt*2.4)
            pygame.mixer.music.set_volume(self.music_level)
        self.update_particles(dt)
        if self.beat.key != "choices" and self.beat.duration > 0 and self.beat_elapsed >= self.beat.duration:
            if self.beat.key == "proposal":
                self.burst(800, 350, 220)
                self.launch_firework(235, 230)
                self.launch_firework(1040, 210)
            self.next_beat()

    def cloud(self, surface: pygame.Surface, x: float, y: float, size: float, alpha: int) -> None:
        layer = pygame.Surface((int(size*4), int(size*1.55)), pygame.SRCALPHA)
        color = (93, 87, 125, alpha)
        for ox, oy, radius in ((.6,.63,.42), (1.15,.4,.49), (1.75,.59,.52), (2.45,.65,.4)):
            pygame.draw.ellipse(layer, color, (int((ox-radius)*size), int((oy-radius*.53)*size), int(radius*2*size), int(radius*1.1*size)))
        surface.blit(layer, (int(x), int(y)))

    def draw_sky(self, surface: pygame.Surface, now: float) -> None:
        surface.blit(self.gradient, (0, 0))
        for i, (x, y, size, speed, phase) in enumerate(self.clouds):
            drift_x = (x + now*speed) % (WIDTH+size*4) - size*2
            self.cloud(surface, drift_x, y + math.sin(now*.18+phase)*9, size, 17 + (i % 3)*5)
        for x, y, radius, phase in self.stars:
            twinkle = .48 + .52 * (math.sin(now*1.6 + phase) + 1) / 2
            col = (int(140+115*twinkle), int(154+94*twinkle), 255)
            if radius > 1.65 and twinkle > .86:
                pygame.draw.line(surface, (*col, 100), (x-5,y), (x+5,y), 1)
                pygame.draw.line(surface, (*col, 100), (x,y-5), (x,y+5), 1)
            pygame.draw.circle(surface, col, (x,y), max(1, round(radius*twinkle)))
        moon_x, moon_y = 1000, 186
        glow(surface, moon_x, moon_y, 145, (204, 167, 202), 40)
        pygame.draw.circle(surface, (255, 237, 213), (moon_x, moon_y), 61)
        pygame.draw.circle(surface, (255, 247, 230), (moon_x-10, moon_y-9), 50)
        pygame.draw.circle(surface, (229, 212, 213), (moon_x+17, moon_y+11), 5)
        pygame.draw.circle(surface, (239, 224, 219), (moon_x-22, moon_y+25), 3)
        surface.blit(self.skyline, (0, 0))
        pygame.draw.polygon(surface, (22, 25, 49), [(0, 564), (110, 503), (235, 551), (376, 482), (521, 558), (687, 490), (825, 553), (1001, 486), (1155, 545), (1280, 500), (1280, 720), (0,720)])
        pygame.draw.polygon(surface, (17, 21, 42), [(0, 610), (174, 558), (345, 615), (542, 548), (705, 607), (884, 553), (1067, 616), (1210, 557), (1280, 580), (1280,720),(0,720)])
        pygame.draw.rect(surface, (19, 21, 40), (0, 620, WIDTH, 100))
        # A few distant warmly lit windows and a reflective promenade.
        pygame.draw.line(surface, (100, 69, 91), (0, 625), (WIDTH, 625), 2)
        for i in range(16):
            px = (i*113 + 30) % WIDTH
            pygame.draw.line(surface, (39, 38, 57), (px, 660+(i%4)*11), (px+70, 660+(i%4)*11), 1)
        glow(surface, 640, 625, 220, (191, 116, 139), 12)

    def draw_fireworks(self, surface: pygame.Surface) -> None:
        palette = ((255, 195, 151), (255, 135, 185), (172, 190, 255), (255, 231, 159))
        for fw in self.fireworks:
            t = float(fw["timer"])
            x, y = int(fw["x"]), int(fw["y"])
            color = palette[int(fw["color"])]
            radius = int(14 + t*72)
            fade = max(0, int(210*(1-t/float(fw["life"]))))
            for j in range(18):
                angle = j*math.tau/18
                px, py = x+math.cos(angle)*radius, y+math.sin(angle)*radius
                pygame.draw.line(surface, (*color, fade), (x+math.cos(angle)*(radius-10),y+math.sin(angle)*(radius-10)), (px,py), 2)
                pygame.draw.circle(surface, color, (round(px),round(py)), max(1, round(2.5*(1-t/1.5))))

    def draw_person(self, surface: pygame.Surface, x: float, floor: float, kind: str, now: float, pose: str = "stand", kneel: float = 0.0, ring: bool = False, surprised: bool = False, walking: bool = False) -> None:
        s = 1.0
        bob = math.sin(now*5.0+(0 if kind=="boy" else 1.6))*2.0 if walking else math.sin(now*1.5)*1.3
        floor += bob
        skin = (240, 190, 164) if kind == "boy" else (250, 202, 180)
        hair = (45, 34, 49) if kind == "boy" else (48, 30, 48)
        outfit = (70, 83, 124) if kind == "boy" else (177, 91, 126)
        scale = 1.0
        hip = (x, floor-87)
        # Limb positions transition continuously into a stable one-knee pose.
        walk = math.sin(now*5.5) * 16 if walking else 0
        if pose == "sit":
            standing_legs = [((x-34, floor-43), (x-52, floor-8)), ((x+34, floor-43), (x+55, floor-8))]
        else:
            standing_legs = [((x-12+walk, floor-48), (x-19+walk, floor-8)), ((x+12-walk, floor-48), (x+18-walk, floor-8))]
        kneeling_legs = [((x-27, floor-9), (x-55, floor-8)), ((x+18, floor-45), (x+38, floor-8))]
        legs = []
        for i, (stand, down) in enumerate(zip(standing_legs, kneeling_legs)):
            knee = (stand[0][0]*(1-kneel)+down[0][0]*kneel, stand[0][1]*(1-kneel)+down[0][1]*kneel)
            foot = (stand[1][0]*(1-kneel)+down[1][0]*kneel, stand[1][1]*(1-kneel)+down[1][1]*kneel)
            legs.append((knee, foot))
        # Rear leg and soft shoe silhouette.
        for index, (knee, foot) in enumerate(legs):
            pygame.draw.line(surface, (38, 34, 51), hip, knee, 19)
            pygame.draw.line(surface, (37, 32, 48), knee, foot, 16)
            pygame.draw.ellipse(surface, (29, 28, 43), (foot[0]-19, foot[1]-7, 39, 15))
        # Coat/dress silhouette, taper, seam and scarf detail.
        body_x = x + kneel*10
        shoulder_y = floor - 157 + kneel*15
        body_bottom = floor - 75 + kneel*4
        pygame.draw.polygon(surface, outfit, [(body_x-33,shoulder_y+9),(body_x-22,shoulder_y-2),(body_x+22,shoulder_y-2),(body_x+34,shoulder_y+9),(body_x+29,body_bottom),(body_x,body_bottom+8),(body_x-31,body_bottom)])
        shade = mix(outfit,(20,23,43),.35)
        pygame.draw.polygon(surface, shade, [(body_x+3,shoulder_y+1),(body_x+23,shoulder_y+4),(body_x+28,body_bottom),(body_x+3,body_bottom+6)])
        pygame.draw.line(surface, (222, 174, 182), (body_x, shoulder_y+8), (body_x-3, body_bottom+4), 2)
        # Head turns toward the other person, shoulders subtly follow.
        face_x = x + (3 if kind == "boy" else -3)
        head_y = floor - 184 + kneel*10 + bob
        pygame.draw.ellipse(surface, skin, (face_x-25,head_y-30,50,58))
        pygame.draw.ellipse(surface, hair, (face_x-28,head_y-36,56,41))
        if kind == "girl":
            pygame.draw.ellipse(surface, hair, (face_x-31,head_y-20,17,57))
            pygame.draw.ellipse(surface, hair, (face_x+13,head_y-18,17,57))
            pygame.draw.polygon(surface, hair, [(face_x-26,head_y-18),(face_x-18,head_y-37),(face_x-3,head_y-27),(face_x+8,head_y-38),(face_x+25,head_y-16),(face_x+18,head_y-9),(face_x-18,head_y-9)])
            pygame.draw.circle(surface, GOLD, (round(face_x+21),round(head_y-23)), 5)
        else:
            pygame.draw.polygon(surface, hair, [(face_x-25,head_y-17),(face_x-21,head_y-35),(face_x-7,head_y-27),(face_x+4,head_y-38),(face_x+24,head_y-18)])
        eye_y = round(head_y-1)
        gaze_dir = 1 if kind == "boy" else -1
        for eye_dx in (-9, 9):
            pygame.draw.circle(surface, (47,34,42), (round(face_x+eye_dx+gaze_dir*2),eye_y), 2)
        pygame.draw.arc(surface, (169,91,106), (face_x-5,head_y+7,11,8), .15, 2.8, 2)
        pygame.draw.ellipse(surface, (229,144,139), (face_x-20,head_y+5,8,4))
        pygame.draw.ellipse(surface, (229,144,139), (face_x+12,head_y+5,8,4))
        # Arms use animated elbow/hand coordinates; the ring stays connected to his hand.
        left_shoulder, right_shoulder = (body_x-25,shoulder_y+16), (body_x+24,shoulder_y+15)
        if kind == "boy":
            arm_pose = kneel
            ring_hand = (x+62, floor-104-45*min(1, max(0,(kneel-.25)*1.6)))
            left_elbow = (x-42, floor-117+arm_pose*10)
            left_hand = (x-35+arm_pose*4, floor-91+arm_pose*5)
            right_elbow = (x+38+arm_pose*17, floor-120+arm_pose*8)
            right_hand = (x+24+arm_pose*38, floor-110-arm_pose*42)
            if ring:
                right_hand = ring_hand
                right_elbow = (x+42+arm_pose*23, floor-125-arm_pose*20)
            pygame.draw.line(surface, outfit, left_shoulder, left_elbow, 14)
            pygame.draw.line(surface, outfit, left_elbow, left_hand, 12)
            pygame.draw.line(surface, outfit, right_shoulder, right_elbow, 14)
            pygame.draw.line(surface, outfit, right_elbow, right_hand, 12)
            pygame.draw.circle(surface, skin, (round(left_hand[0]),round(left_hand[1])), 7)
            pygame.draw.circle(surface, skin, (round(right_hand[0]),round(right_hand[1])), 7)
            if ring:
                glow(surface, right_hand[0]+5, right_hand[1]-11, 25, GOLD, 120)
                pygame.draw.circle(surface, GOLD, (round(right_hand[0]+5),round(right_hand[1]-12)), 8, 3)
                pygame.draw.circle(surface, (255,255,228), (round(right_hand[0]+5),round(right_hand[1]-19)), 4)
                pygame.draw.line(surface, (255,241,188), (right_hand[0]+8,right_hand[1]-25), (right_hand[0]+8,right_hand[1]-35), 2)
        elif surprised:
            for side, shoulder in ((-1,left_shoulder),(1,right_shoulder)):
                elbow=(x+side*37,floor-144)
                hand=(x+side*24,floor-181)
                pygame.draw.line(surface,outfit,shoulder,elbow,13)
                pygame.draw.line(surface,outfit,elbow,hand,12)
                pygame.draw.circle(surface,skin,(round(hand[0]),round(hand[1])),8)

    def positions(self, key: str, t: float) -> tuple[float,float,str,bool,bool]:
        """Return boy x, girl x, pose, ring visibility, girl surprise."""
        pose, ring, surprise = "stand", False, False
        boy_x, girl_x = 473.0, 822.0
        if key == "city":
            boy_x = -90 + 563*ease(t/4.5)
        elif key in {"notice", "spellbound"}:
            boy_x = 482
        elif key == "montage_walk":
            boy_x, girl_x, pose = 557, 712, "walk"
        elif key == "montage_moon":
            boy_x, girl_x, pose = 566, 715, "sit"
        elif key == "montage_gaze":
            boy_x, girl_x = 604, 698
        elif key == "montage_petals":
            boy_x, girl_x, pose = 552, 721, "walk"
        elif key == "montage_fireworks":
            boy_x, girl_x = 590, 692
        elif key == "heart_effect":
            boy_x, girl_x = 590, 700
        elif key in {"walk_together", "life_1", "life_2", "stop", "breath", "reach", "kneel", "question_intro", "proposal", "choices", "accept", "forever"}:
            approach = ease(t/4.0) if key == "walk_together" else 1.0
            boy_x, girl_x = 530+94*approach, 822
        if key in {"reach", "kneel", "question_intro", "proposal", "choices", "accept", "forever"}:
            ring = key in {"reach", "kneel", "question_intro", "proposal", "choices", "accept", "forever"}
            kneel = ease((t-0.10)/2.65) if key == "kneel" else (1.0 if key in {"question_intro", "proposal", "choices", "accept", "forever"} else 0.0)
            pose = f"kneel:{kneel:.3f}"
            surprise = key in {"question_intro", "proposal", "choices", "accept", "forever"}
        if key == "stop":
            boy_x = 624
        return boy_x, girl_x, pose, ring, surprise

    def caption_text(self, key: str, t: float) -> str:
        if key.startswith("found_"):
            return self.beat.caption if t > .45 else ""
        if key == "city":
            return f"{BOY_NAME} was just another face in the city..." if t > 2.3 else ""
        if key == "walk_together":
            return f"{BOY_NAME} kept finding his way back to {GIRL_NAME}." if t < 4 else ""
        if key == "montage_walk":
            return f"{GIRL_NAME} became his favorite thought."
        if key in {"life_1", "life_2", "notice", "spellbound", "montage_walk", "montage_moon", "montage_gaze", "montage_petals", "montage_fireworks", "heart_effect", "question_intro", "proposal", "accept"}:
            return self.beat.caption
        return ""

    def draw_scene(self, surface: pygame.Surface, now: float) -> None:
        surface.fill(INK)
        key, t = self.beat.key, self.beat_elapsed
        if key.startswith("found_") or key == "dark":
            alpha = 0 if key == "dark" else int(255*ease(t/.6))
            glow(surface, 640, 345, round(20+16*math.sin(now*2.0)), ROSE, round(170*ease(t/.8)))
            draw_heart(surface, 640, 345, 15+3*math.sin(now*2), ROSE, alpha, True)
            return
        self.draw_sky(surface, now)
        for particle in self.ambient:
            particle.draw(surface)
        key = self.beat.key
        boy_x, girl_x, pose, ring, surprise = self.positions(key, t)
        # First-sight illusion: gently wash out the city and isolate her in moonlight.
        first_sight = ease((t-1.0)/1.8) if key == "notice" else (1.0 if key in {"spellbound", "montage_walk", "montage_moon", "montage_gaze", "montage_petals", "montage_fireworks", "heart_effect", "walk_together", "life_1", "life_2", "stop", "breath", "reach", "kneel", "question_intro", "proposal", "choices", "accept", "forever"} else 0.0)
        if first_sight:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((8, 8, 22, round(112*first_sight)))
            surface.blit(shade,(0,0))
            glow(surface, int(girl_x), 463, 190, (255,178,166), round(70*first_sight))
        if key == "heart_effect":
            pulse = 1 + .15*math.sin(t*math.tau*1.4)
            glow(surface, boy_x, 533, round(47*pulse), (255,75,139), 115)
            draw_heart(surface,boy_x,533,round(22*pulse),(255,91,155),halo=True)
            q=clamp((t-1.2)/2.8,0,1)
            start=(boy_x+18,533)
            end=(girl_x-26,517)
            pygame.draw.line(surface,(255,184,218),start,(start[0]+(end[0]-start[0])*q,start[1]+(end[1]-start[1])*q),3)
            if q>0:
                glow(surface,start[0]+(end[0]-start[0])*q,start[1]+(end[1]-start[1])*q,18,ROSE,140)
            if t>4.05:
                heart_size=clamp((t-4.05)/.75,0,1)
                pygame.draw.arc(surface,(255,159,204),(boy_x-63,382,160,171),.1,3.05,3)
                pygame.draw.arc(surface,(255,159,204),(boy_x-63,382,160,171),3.2,6.18,3)
                if heart_size>0:
                    draw_heart(surface,(boy_x+girl_x)/2,426,round(75*heart_size),ROSE,alpha=65,halo=True)
        walk = key in {"montage_walk","montage_petals","walk_together"}
        if key == "montage_fireworks":
            for fw_x in (160,1100):
                glow(surface,fw_x,315,42,(255,151,194),36)
        kneel = float(pose.split(":")[1]) if pose.startswith("kneel:") else 0
        ground = 632
        if pose == "sit":
            # Both figures share a grounded seated pose against the lake path.
            for person_x in (boy_x, girl_x):
                pygame.draw.ellipse(surface, (10, 11, 24), (round(person_x-42), ground-12, 84, 15))
            self.draw_person(surface,boy_x,ground, "boy",now,"sit",walking=False)
            self.draw_person(surface,girl_x,ground,"girl",now,"sit",walking=False)
        else:
            for person_x in (boy_x, girl_x):
                pygame.draw.ellipse(surface, (10, 11, 24), (round(person_x-39), ground-10, 78, 13))
            self.draw_person(surface,boy_x,ground,"boy",now,"stand",kneel,ring,walking=walk and not kneel)
            self.draw_person(surface,girl_x,ground,"girl",now,"stand",0,False,surprise)
        if key in {"notice","spellbound"} and first_sight:
            for i in range(5):
                phase=now*1.5+i*math.tau/5
                draw_heart(surface,boy_x+math.cos(phase)*52,ground-191+math.sin(phase)*27,7,(255,130,179),halo=i==0)
        if key in {"walk_together","life_1","life_2","stop","breath","reach","kneel","question_intro","proposal","choices","accept","forever"}:
            progress=clamp(t/3.3,0,1) if key=="walk_together" else 1
            for i in range(int(progress*7)):
                draw_heart(surface,530+i*19,ground-3,4,(255,147,190),alpha=130)
        for petal in self.petals:
            petal.draw(surface)
        for particle in self.heart_particles:
            particle.draw(surface)
        self.draw_fireworks(surface)
        # Subtle vignette and cinematic letterboxing.
        vignette=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        for i in range(8):
            alpha=5+i*2
            pygame.draw.rect(vignette,(5,5,18,alpha),(i*8,i*5,WIDTH-i*16,HEIGHT-i*10),width=10)
        surface.blit(vignette,(0,0))

    def draw_screen_text(self, surface: pygame.Surface, text: str, x: int, y: int, size: int, color: tuple[int,int,int], alpha: int=255, align: str="center", bold: bool=False) -> None:
        font=self.font(size,bold)
        lines=text.split("\n")
        for index,line in enumerate(lines):
            rendered=font.render(line,True,color)
            if alpha<255:
                rendered.set_alpha(max(0,alpha))
            rect=rendered.get_rect()
            rect.midtop=(x,y+index*(size+10)) if align=="center" else (x,y+index*(size+10))
            if align=="left": rect.topleft=(x,y+index*(size+10))
            surface.blit(rendered,rect)

    def draw_caption(self, surface: pygame.Surface, text: str) -> None:
        if not text:
            return
        t=self.beat_elapsed
        alpha=round(255*ease(min(t/.42,(self.beat.duration-t)/.55)))
        strip=pygame.Surface((WIDTH,158),pygame.SRCALPHA)
        for row in range(158):
            strip.fill((7,7,19,round(125*(1-row/158))),rect=(0,row,WIDTH,1))
        surface.blit(strip,(0,HEIGHT-160))
        lines=text.split("\n")
        font_size=33 if len(lines)==1 else 30
        total_h=len(lines)*(font_size+9)
        y=HEIGHT-95-total_h//2
        for i,line in enumerate(lines):
            font=self.font(font_size,False)
            text_surface=font.render(line,True,CREAM)
            text_surface.set_alpha(max(0,alpha))
            text_rect=text_surface.get_rect(center=(WIDTH//2,y+i*(font_size+9)+font_size//2))
            shadow=font.render(line,True,(16,10,27))
            shadow.set_alpha(max(0,alpha//2))
            surface.blit(shadow,text_rect.move(2,3))
            surface.blit(text_surface,text_rect)

    def draw_choices(self, surface: pygame.Surface) -> None:
        t=self.beat_elapsed
        alpha=round(255*ease((t-1.4)/.8))
        glow(surface,640,581,230,(218,111,160),35)
        self.draw_screen_text(surface,"Choose the next page of your story",640,536,20,(246,212,224),alpha)
        self.choice_hotspots=[]
        for rect,label in ((pygame.Rect(336,602,256,66),"YES"),(pygame.Rect(688,602,256,66),"ABSOLUTELY")):
            pulse=1+.025*math.sin(self.elapsed*3)
            scaled=rect.inflate(round(rect.width*(pulse-1)),round(rect.height*(pulse-1)))
            layer=pygame.Surface((scaled.width,scaled.height),pygame.SRCALPHA)
            pygame.draw.rect(layer,(144,59,105,alpha),(0,0,scaled.width,scaled.height),border_radius=33)
            pygame.draw.rect(layer,(255,218,224,alpha),(0,0,scaled.width,scaled.height),width=2,border_radius=33)
            surface.blit(layer,scaled.topleft)
            self.draw_screen_text(surface,label,scaled.centerx,scaled.centery-14,23,CREAM,alpha, bold=True)
            draw_heart(surface,scaled.right-25,scaled.centery,7,(255,186,200),alpha)
            self.choice_hotspots.append((scaled,label))
        self.draw_screen_text(surface,"A whole future of little moments starts with one click.",640,683,16,(190,171,192),alpha)

    def choose(self, label: str) -> None:
        if self.answer or self.beat.key != "choices":
            return
        self.answer=label
        self.beat_index=STORY.index(next(beat for beat in STORY if beat.key=="accept"))
        self.beat_elapsed=0
        self.update_music()
        self.burst(640,360,240)
        for x in (190,640,1090):
            self.launch_firework(x,self.rng.uniform(125,265))

    def leave_fullscreen(self, event: pygame.event.Event | None = None) -> None:
        """Switch to the windowed game view; safe for direct and event calls."""
        _ = event
        if not self.fullscreen:
            self.running = False
            return
        self.fullscreen = False
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE, vsync=1)

    def handle_event(self,event: pygame.event.Event) -> None:
        if event.type==pygame.QUIT:
            self.running=False
        elif event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                self.leave_fullscreen(event)
            elif event.key==pygame.K_q:
                self.running=False
            elif event.key==pygame.K_F11:
                self.fullscreen=not self.fullscreen
                flags=pygame.FULLSCREEN|pygame.SCALED|pygame.DOUBLEBUF if self.fullscreen else pygame.SCALED|pygame.RESIZABLE
                self.screen=pygame.display.set_mode((WIDTH,HEIGHT),flags,vsync=1)
            elif event.key in (pygame.K_PLUS,pygame.K_EQUALS,pygame.K_UP):
                self.music_volume=clamp(self.music_volume+.05,0,1)
                self.update_music()
            elif event.key in (pygame.K_MINUS,pygame.K_DOWN):
                self.music_volume=clamp(self.music_volume-.05,0,1)
                self.update_music()
            elif event.key in (pygame.K_1,pygame.K_y):
                self.choose("YES")
            elif event.key in (pygame.K_2,pygame.K_a):
                self.choose("ABSOLUTELY")
            elif event.key==pygame.K_SPACE and self.beat_elapsed>.9 and self.beat.key not in {"choices","accept","forever"}:
                if self.beat.key=="proposal": self.burst(800,350,220)
                self.next_beat()
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for rect,label in self.choice_hotspots:
                if rect.collidepoint(event.pos):
                    self.choose(label)

    def current_scene_volume(self) -> float:
        key=self.beat.key
        if key in {"dark","found_1","found_2","found_3","found_4"}: return .16
        if key in {"proposal","question_intro","stop","breath"}: return .24
        if key in {"accept","forever"}: return .85
        return .53

    def draw_interface(self, screen: pygame.Surface, now: float) -> None:
        key=self.beat.key
        caption=self.caption_text(key,self.beat_elapsed)
        if key.startswith("found_"):
            shown=caption
            chars=min(len(shown),int(max(0,self.beat_elapsed-.25)*25))
            self.draw_screen_text(screen,shown[:chars],640,491,32,CREAM,round(255*ease(self.beat_elapsed/.5)))
        else:
            self.draw_caption(screen,caption)
        if key=="proposal":
            pulse=1+.035*math.sin(now*2.2)
            size=round(51*pulse)
            glow(screen,640,287,150,GOLD,95)
            self.draw_screen_text(screen,PROPOSAL_MESSAGE,640,259,size,GOLD,round(255*ease((self.beat_elapsed-1.0)/1.4)),bold=True)
        if key=="choices":
            self.draw_choices(screen)
        if key=="accept":
            draw_heart(screen,640,204,27,(255,136,184),halo=True)
            self.draw_screen_text(screen,"Forever Starts Here",640,247,43,CREAM,round(255*ease(self.beat_elapsed/.7)),bold=True)
        if key=="forever":
            self.draw_screen_text(screen,"I Love You Forever",640,282,50,GOLD,round(255*ease(self.beat_elapsed/.8)),bold=True)
            draw_heart(screen,515,300,15,ROSE,halo=True)
            draw_heart(screen,765,300,15,ROSE,halo=True)
        if self.music_notice and self.music_notice_elapsed<9:
            alpha=round(220*min(1,(9-self.music_notice_elapsed)/1))
            panel=pygame.Surface((WIDTH,48),pygame.SRCALPHA)
            pygame.draw.rect(panel,(10,9,23,alpha),(0,0,WIDTH,48))
            screen.blit(panel,(0,0))
            msg=f"Setup note: {MUSIC_FILE} not found — playing the original built-in score. Add your MP3 beside main.py to use it."
            self.draw_screen_text(screen,msg,WIDTH//2,13,16,(235,214,225),alpha)
        elif not self.music_available:
            self.draw_screen_text(screen,"Audio device unavailable — story continues; connect audio and restart for music.",WIDTH//2,14,16,(255,210,211))
        # Small custom-drawn volume meter, not a standard GUI control.
        pygame.draw.line(screen,(186,164,185),(24,HEIGHT-28),(100,HEIGHT-28),2)
        pygame.draw.line(screen,GOLD,(24,HEIGHT-28),(24+76*self.music_volume,HEIGHT-28),3)
        pygame.draw.circle(screen,CREAM,(round(24+76*self.music_volume),HEIGHT-28),5)
        label=self.font(13).render("MUSIC  − / +",True,(198,181,202))
        screen.blit(label,(22,HEIGHT-51))
        self.draw_screen_text(screen,"SPACE: skip beat   •   F11: fullscreen   •   ESC: leave",WIDTH//2,HEIGHT-28,13,(151,141,169))

    def draw(self) -> None:
        now=self.elapsed
        self.draw_scene(self.scene,now)
        key=self.beat.key
        zoom=.0
        if key in {"notice","spellbound"}:
            zoom=.035*ease((self.beat_elapsed+.5)/self.beat.duration)
        elif key in {"montage_walk","montage_moon","montage_gaze","montage_petals","montage_fireworks"}:
            zoom=.018*math.sin(math.pi*self.beat_elapsed/self.beat.duration)
        elif key in {"heart_effect","walk_together","life_1","life_2","kneel","question_intro","proposal","choices","accept","forever"}:
            zoom=.05*ease(self.beat_elapsed/max(1,self.beat.duration))
        if key in {"proposal","choices","accept","forever"}:
            zoom+=.02*math.sin(now*1.4)
        scale=max(1.0,1+zoom)
        camera=pygame.transform.smoothscale(self.scene,(round(WIDTH*scale),round(HEIGHT*scale))) if scale>1.003 else self.scene
        self.screen.fill((4,4,14))
        self.screen.blit(camera,((WIDTH-camera.get_width())//2,(HEIGHT-camera.get_height())//2))
        if key != "dark" and self.beat_elapsed < .55:
            transition=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            transition.fill((2,2,12,round(255*(1-ease(self.beat_elapsed/.55)))))
            self.screen.blit(transition,(0,0))
        if key in {"notice","spellbound","stop","breath","question_intro","proposal","choices","accept","forever"}:
            darkness=.15 if key in {"notice","spellbound"} else .22
            dim=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            dim.fill((5,4,16,round(100*darkness)))
            self.screen.blit(dim,(0,0))
        if key in {"accept","forever"}:
            # Finale's hundreds of independently animated particles, kept bounded for 60 FPS.
            if len(self.heart_particles)>440:
                self.heart_particles=self.heart_particles[-440:]
        self.draw_interface(self.screen,now)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt=min(self.clock.tick(FPS)/1000, .04)
            for event in pygame.event.get():
                self.handle_event(event)
            if self.beat.key=="choices" and self.beat_elapsed>=STORY[self.beat_index].duration:
                self.beat_elapsed=STORY[self.beat_index].duration
            self.update(dt)
            self.draw()
        if pygame.mixer.get_init():
            pygame.mixer.music.fadeout(350)
            pygame.mixer.quit()
        pygame.quit()


def main() -> None:
    ProposalGame().run()


if __name__ == "__main__":
    main()
