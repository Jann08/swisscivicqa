// Shared data and helpers; all numbers come from results/expected/apertus-v1.5-8b-text-q8_0.json.
#let m = json("../results/expected/apertus-v1.5-8b-text-q8_0.json")
#let pct(x) = str(calc.round(x * 100, digits: 1)) + "%"
#let L = ("de": "German", "fr": "French", "it": "Italian", "rm": "Romansh")
#let langs = ("de", "fr", "it", "rm")
#let ink2 = rgb("#52514e")
#let q = json("../results/expected/qwen3-8b-q8_0.json")
#let c = json("../results/expected/comparison.json")

// Design tokens and components
#let accent = rgb("#b3122e")
#let paper2 = rgb("#f6f5f1")
#let rule = rgb("#e2dfd8")
#let sans = ("Lato", "Liberation Sans", "DejaVu Sans")
#let stat(value, label) = block(width: 100%, height: 50pt, inset: (x: 8pt, y: 7pt), radius: 3pt, fill: paper2)[
  #set par(justify: false, leading: 0.45em)
  #set text(hyphenate: false)
  #text(font: sans, size: 17pt, weight: "bold", fill: accent, value)\
  #v(-4pt)
  #text(font: sans, size: 7.5pt, fill: ink2, label)
]
#let finding(n, title, body) = {
  // Title is sticky so it never ends up alone at the bottom of a page.
  block(width: 100%, sticky: true, above: 1em, below: 0pt, stroke: (left: 2pt + accent), inset: (left: 9pt, top: 2pt, bottom: 6pt),
    text(font: sans, size: 9.5pt, weight: "bold")[#text(fill: accent)[#n] #h(3pt) #title])
  block(width: 100%, above: 0pt, below: 1em, stroke: (left: 2pt + accent), inset: (left: 9pt, bottom: 2pt), body)
}
