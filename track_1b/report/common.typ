// Shared data and helpers; all numbers come from results/expected_metrics.json.
#let m = json("../results/expected_metrics.json")
#let pct(x) = str(calc.round(x * 100, digits: 1)) + "%"
#let L = ("de": "German", "fr": "French", "it": "Italian", "rm": "Romansh")
#let langs = ("de", "fr", "it", "rm")
#let ink2 = rgb("#52514e")
