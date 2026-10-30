"""Generates the schematics in docs/images. Run from the repo root: python3 docs/diagrams.py"""
import matplotlib; matplotlib.use('Agg')
import schemdraw
import schemdraw.elements as elm

OUT = 'docs/images/'
PREVIEW = None  # set to a directory to also write PNG previews


def pin(p, n, dx, dy):
    elm.Label().at((p[0] + dx, p[1] + dy)).label(n, fontsize=9, color='#ff8a80')


def save(d, name):
    d.save(OUT + name + '.svg', transparent=True)
    # d.save(OUT + name + '.png', dpi=150, transparent=True)
    if PREVIEW:
        d.save(PREVIEW + name + '.png', dpi=150, transparent=True)


# Sender input channel: PC817 isolates the Nano from the 12 V system.
with schemdraw.Drawing(show=False) as d:
    d.config(unit=3, fontsize=11, color='white')
    oc = elm.Optocoupler(color='white').label('U1 PC817', loc='top', ofst=.3)
    # 12 V side
    elm.Line().left(.6).at(oc.anode).dot()
    a = d.here
    elm.Resistor().up().label('$R_1$\n2.2 kΩ', loc='top')
    elm.Dot(open=True).fill('#0d1117').label('+12 V', loc='right')
    elm.Line().left(.6).at(oc.cathode).dot()
    k = d.here
    elm.Line().down(1)
    elm.Dot(open=True).fill('#0d1117').label('Switched\nground wire', loc='right')
    # D1 across the LED, reversed: cathode on the anode (pin 1) side
    elm.Line().left(1.3).at(a)
    elm.Diode().down().reverse().toy(k).label('$D_1$\n1N4148', loc='top')
    elm.Line().tox(k)
    pin(oc.anode, '1', -.3, .2)
    pin(oc.cathode, '2', -.3, -.2)
    pin(oc.emitter, '3', .2, .15)
    pin(oc.collector, '4', .2, -.15)
    # Nano side
    elm.Line().up(.6).at(oc.collector).dot()
    c = d.here
    elm.Line().right(1.2)
    elm.Dot(open=True).fill('#0d1117').label('Nano D6 (D7)', loc='right')
    elm.Resistor().up().at(c).label('internal\npull-up', loc='bottom')
    elm.Vdd().label('+5 V')
    elm.Line().down(.5).at(oc.emitter)
    elm.Ground()
save(d, 'sender-input')

# Receiver output channel: TIP125 high-side switch. Its base is pulled down by
# either the Nano path (2N3904) or the wired backup path (PC817), OR-ed together.
with schemdraw.Drawing(show=False) as d:
    d.config(unit=3, fontsize=11, color='white')
    yb, yg = 8, 3  # base bus height, ground rail height

    # Q1 TIP125 high-side switch
    q1 = elm.BjtPnp().at((12, yb)).anchor('base').label('$Q_1$\nTIP125', loc='right')
    pin(q1.base, '1', -.2, .2)
    pin(q1.collector, '2', .2, -.15)
    pin(q1.emitter, '3', .2, .15)
    elm.Line().up(.8).at(q1.emitter)
    elm.Vdd().label('+12 V (fused)\nreceiver supply')
    elm.Line().down(.8).at(q1.collector)
    elm.Line().right(1.5)
    elm.Dot(open=True).fill('#0d1117').label('Lamp wire\n(switched +12 V)', loc='right')

    # base node bus
    elm.Line().at(q1.base).tox(2.5)
    elm.Dot().at((7, yb))

    # Nano path: R2 -> Q2 2N3904 (base fed from D3/D5 through R1)
    r2 = elm.Resistor().down().at((7, yb)).length(2.2).label('$R_2$\n2.2 kΩ', loc='top')
    q2 = elm.BjtNpn().right().reverse().anchor('collector').at(r2.end).label('$Q_2$\n2N3904', loc='left')
    pin(q2.collector, '3', -.3, -.1)
    pin(q2.base, '2', .2, .2)
    pin(q2.emitter, '1', -.3, -.1)
    elm.Line().down().toy(yg).at(q2.emitter)
    elm.Line().right(.6).at(q2.base)
    elm.Resistor().right().length(2.2).label('$R_1$\n1 kΩ', loc='top')
    elm.Dot(open=True).fill('#0d1117').label('Nano D3 (D5)', loc='right')

    # Wired backup path: R4 -> U1 PC817 (LED driven from the wired source)
    r4 = elm.Resistor().down().at((2.5, yb)).length(2).label('$R_4$\n4.7 kΩ', loc='bottom')
    u1 = elm.Optocoupler(color='white').right().anchor('collector').at(r4.end).label('U1 PC817', loc='top', ofst=.3)
    pin(u1.anode, '1', -.3, .2)
    pin(u1.cathode, '2', -.3, -.2)
    pin(u1.emitter, '3', .2, .15)
    pin(u1.collector, '4', .2, -.15)
    elm.Line().down().toy(yg).at(u1.emitter)

    # wired source side
    elm.Line().left(.6).at(u1.anode)
    elm.Dot()
    na = d.here
    elm.Resistor().left().length(2).label('$R_3$\n2.2 kΩ', loc='top')
    elm.Line().left(.5)
    elm.Dot(open=True).fill('#0d1117').label('Wired +12 V', loc='left')
    elm.Line().left(.6).at(u1.cathode)
    elm.Dot()
    nk = d.here
    elm.Line().left(2.5)
    elm.Dot(open=True).fill('#0d1117').label('Wired switched\nground wire', loc='left')
    elm.Diode().at(nk).up().toy(na).label('$D_1$\n1N4148', loc='top')

    # ground rail
    elm.Line().at((2.5, yg)).tox(q2.emitter[0])
    elm.Ground().at((5, yg))
    elm.Dot().at((5, yg))
    elm.Label().at((5, yg - 1.4)).label('receiver 12 V ground\n(lamp ground, Nano GND)', fontsize=10)
save(d, 'receiver-output')
