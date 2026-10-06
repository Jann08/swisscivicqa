import json
import unittest
from pathlib import Path

from swisscivicqa import grade, parse, score, validate

ROOT = Path(__file__).resolve().parents[1]


def item(answer_type, gold, aliases=(), lang="de"):
    return {"answer_type": answer_type, "gold_answer": gold, "gold_aliases": list(aliases), "language": lang}


class TestNumbers(unittest.TestCase):
    def test_thousands_separators_are_normalised(self):
        for text in ("100'000", "100 000", "100 000", "100.000", "100000"):
            self.assertIn("100000", grade.numbers(text), text)

    def test_number_words(self):
        self.assertIn("6", grade.numbers("Sechs Monate.", "de"))
        self.assertIn("7", grade.numbers("Set.", "rm"))
        self.assertEqual(grade.rule_grade(item("number", "18"), "Sechs Monate."), "INCORRECT")

    def test_decimal_comma(self):
        self.assertIn("11.5", grade.numbers("11,5 Prozent"))


class TestRuleGrade(unittest.TestCase):
    def test_number_correct_and_incorrect(self):
        it = item("number", "100 000")
        self.assertEqual(grade.rule_grade(it, "Es braucht 100'000 Unterschriften."), "CORRECT")
        self.assertEqual(grade.rule_grade(it, "80 000."), "INCORRECT")

    def test_number_with_extra_numbers_is_left_to_judge(self):
        self.assertIsNone(grade.rule_grade(item("number", "100 000"), "100 000 in 18 Monaten"))

    def test_yes_no_per_language(self):
        self.assertEqual(grade.rule_grade(item("yes_no", "Nein"), "Nein, das ist ausgeschlossen."), "CORRECT")
        self.assertEqual(grade.rule_grade(item("yes_no", "Gea", lang="rm"), "Na."), "INCORRECT")
        self.assertEqual(grade.rule_grade(item("yes_no", "Sì", lang="it"), "Sì, è vietata."), "CORRECT")

    def test_entity_items_are_not_rule_graded(self):
        self.assertIsNone(grade.rule_grade(item("entity", "die Bundesversammlung"), "Die Bundesversammlung."))


class TestScore(unittest.TestCase):
    def test_rates(self):
        r = score.rates(["CORRECT", "CORRECT", "INCORRECT", "NOT_ATTEMPTED"])
        self.assertEqual((r["accuracy"], r["correct_given_attempted"], r["hallucination_rate"]), (0.5, 0.6667, 0.3333))

    def test_kappa_perfect_and_chance(self):
        self.assertEqual(score.cohen_kappa(["A", "B"], ["A", "B"]), 1.0)
        self.assertEqual(score.cohen_kappa(["A", "A", "B", "B"], ["A", "B", "A", "B"]), 0.0)


class TestParse(unittest.TestCase):
    def test_nested_lists_are_attached_to_paragraph(self):
        body = '<p class="absatz"><sup>1</sup> Intro:</p><dl><dt>a.</dt><dd>x<dl><dt>1.</dt><dd>y</dd></dl></dd></dl>'
        blocks = list(parse.blocks(body))
        self.assertEqual([k for k, _ in blocks], ["p", "dl"])
        self.assertIn("y", parse.clean(blocks[1][1]))


class TestDatasetIntegrity(unittest.TestCase):
    def test_all_facts_grounded_in_official_text(self):
        self.assertEqual(validate.check(validate.load_facts()), [])

    def test_built_dataset_matches_sources(self):
        rows = [json.loads(l) for l in open(ROOT / "data" / "dataset" / "eval.jsonl", encoding="utf-8")]
        self.assertEqual(len(rows), len(validate.load_facts()) * len(validate.LANGS))
        self.assertEqual(len({r["id"] for r in rows}), len(rows))


if __name__ == "__main__":
    unittest.main()
