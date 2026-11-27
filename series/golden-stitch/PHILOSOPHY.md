# Golden Stitch — an algorithmic philosophy

*Seria okładek wydawnictwa Roberta Tomeckiego. Każda książka serii rośnie z tego samego algorytmu;
zmienia się tylko „ścieg” (element), paleta i seed.*

**Golden Stitch** holds that every made thing is counted. A crocheter counts stitches in a round, a
gardener counts seeds in a head, a sunflower counts nothing and still lands on 34 and 55. The movement
takes that quiet arithmetic of growth and lets it become the image: an object that is built one unit at
a time, each unit turned by the same irrational angle, until spirals appear that nobody drew.

The engine is Vogel's model of phyllotaxis. Unit *n* is placed at angle *n · 137.507764°* — the golden
angle, the turn that never repeats — and at radius *c·√n*, so every unit claims the same area. Out of
this single rule the eye finds the parastichies: families of 13, 21, 34 spiral arms winding in both
directions. Color is never painted on; it is assigned by arithmetic. A unit's arm is *n mod F* for a
Fibonacci *F*, so stripes run along one family of spirals while the other family cuts across them, and
colour changes at rounds whose sizes are Fibonacci numbers — exactly where a maker would change yarn.
This must be a meticulously crafted algorithm: the golden angle exact to six decimals, the area rule
honoured, nothing approximated for convenience.

The unit is the soul of each book. For a crochet book the unit is a chain link — a loop of plied yarn,
rotated to lie along its spiral, its size taken from the local spacing so neighbours touch the way real
stitches do. Each loop is rendered as yarn, not as a circle: a body stroke, a shadow arc on the side away
from the light, a highlight arc, and a few short diagonal ply marks that twist in one direction. Seeded
noise breathes through position, angle and tension by a fraction of a stitch, because hand-made work is
never perfect and the algorithm should feel like it was refined over countless iterations until the
irregularity reads as touch rather than error.

Composition obeys φ at every scale. The cover is divided by the golden section; the spiral's centre sits
on a golden point, never in the middle, and the growth is allowed to run past the trim so the viewer
feels it continuing. The title lives in a calm band of solid colour whose height is the minor section of
the page. One long tail of yarn leaves the outermost round and drifts away — the only free line in an
otherwise counted world. Every proportion is the product of painstaking optimisation by someone at the
top of the field: balance between dense centre and open edge, between the warm stripes and the dark
ground, between order you can count and texture you can feel.

Seeded variation is the point of a series. The same seed must always produce the same cover; a new seed
produces a sibling, recognisably of the family. Palettes are small and deliberate — a deep ground and
three or four yarn colours chosen to glow against it — so that a shelf of Golden Stitch books reads as one
publisher from a thumbnail of 160 pixels. The beauty is in the process: run the algorithm and watch a
spiral nobody designed assemble itself, stitch by counted stitch, with master-level care.

## Parametry (dla każdej książki serii)
- `unit` – element: `chain` (szydełko), w przyszłości np. `seed`, `cell`, `tile`
- `count` – liczba elementów (≈ 900–2200)
- `armsF` – liczba Fibonacciego dla pasów kolorów wzdłuż spiral (13, 21, 34)
- `roundsF` – czy zmieniać kolor na rundach o rozmiarach Fibonacciego
- `jitter` – oddech szumu (ułamek ściegu)
- `cx, cy` – środek spirali w złotym punkcie strony
- paleta: tło + 3–4 kolory przędzy
- `seed`
