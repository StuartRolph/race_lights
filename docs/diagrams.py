"""Generates the schematics in docs/images. Run from the repo root: python3 docs/diagrams.py"""
import matplotlib; matplotlib.use('Agg')
import schemdraw
import schemdraw.elements as elm

OUT = 'docs/images/'


def pin(p, n, dx, dy):
    elm.Label().at((p[0] + dx, p[1] + dy)).label(n, fontsize=9, color='#ff8a80')


def save(d, name):
    d.save(OUT + name + '.svg', transparent=True)
    # d.save(OUT + name + '.png', dpi=150, transparent=True)


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

# Receiver output channel: TIP125 high-side switch driven through a 2N3904.
with schemdraw.Drawing(show=False) as d:
    d.config(unit=3, fontsize=11, color='white')
    q1 = elm.BjtPnp().label('$Q_1$\nTIP125', loc='right')
    elm.Line().up(.8).at(q1.emitter)
    elm.Vdd().label('+12 V\n(fused)')
    elm.Line().down(.8).at(q1.collector).dot()
    elm.Line().right(1.5)
    elm.Dot(open=True).fill('#0d1117').label('Lamp wire\n(switched +12 V)', loc='right')
    pin(q1.base, '1', -.2, .2)
    pin(q1.collector, '2', .2, -.15)
    pin(q1.emitter, '3', .2, .15)
    # base network
    elm.Line().left(.8).at(q1.base)
    elm.Resistor().down().label('$R_2$\n2.2 kΩ', loc='top')
    q2 = elm.BjtNpn().right().anchor('collector').label('$Q_2$\n2N3904', loc='right')
    pin(q2.emitter, '1', .2, -.1)
    pin(q2.base, '2', -.2, .2)
    pin(q2.collector, '3', .2, .1)
    elm.Ground().at(q2.emitter)
    elm.Resistor().left().at(q2.base).label('$R_1$\n1 kΩ', loc='top')
    elm.Dot(open=True).fill('#0d1117').label('Nano D6 (D7)', loc='left')
save(d, 'receiver-output')
