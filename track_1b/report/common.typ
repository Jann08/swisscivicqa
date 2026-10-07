// Shared data and helpers; all numbers come from results/expected/apertus-v1.5-8b-text-q8_0.json.
#let m = json("../results/expected/apertus-v1.5-8b-text-q8_0.json")
#let pct(x) = str(calc.round(x * 100, digits: 1)) + "%"
#let L = ("de": "German", "fr": "French", "it": "Italian", "rm": "Romansh")
#let langs = ("de", "fr", "it", "rm")
#let ink2 = rgb("#52514e")
#let q = json("../results/expected/qwen3-8b-q8_0.json")
#let c = json("../results/expected/comparison.json")
