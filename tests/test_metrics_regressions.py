"""Regression coverage for consistency of counts from the same fault population."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" /
          "test-verification-design" / "scripts" / "metrics.py")
SPEC = importlib.util.spec_from_file_location("testability_metrics", SCRIPT)
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)


def assessment(total, detected, critical, intersection):
    return {"mode": "count_assessment", "metrics": ["CFDR"], "counts": {
        "faults": total, "detected": detected, "critical_faults": critical,
        "detected_critical_faults": intersection}}


class CountIntersectionTests(unittest.TestCase):
    def test_small_populations_obey_set_intersection_bounds(self):
        # Enumerate every upper-bound-valid combination, including both exact
        # lower bounds, rather than testing only the originally reported tuple.
        for total in range(1, 7):
            for detected in range(total + 1):
                for critical in range(1, total + 1):
                    for intersection in range(min(detected, critical) + 1):
                        with self.subTest(total=total, detected=detected,
                                          critical=critical, intersection=intersection):
                            data = assessment(total, detected, critical, intersection)
                            if intersection < max(0, detected + critical - total):
                                with self.assertRaises(metrics.InputError):
                                    metrics.calculate(data)
                            else:
                                result = metrics.calculate(data)
                                self.assertEqual(result["results"]["CFDR"]["ratio"],
                                                 intersection / critical)
                                self.assertEqual(result["conformity"], "未判定")
                                self.assertIsNone(result["confidence_limits"])

    def test_cfdr_without_optional_total_counts_stays_supported(self):
        data = {"mode": "count_assessment", "metrics": ["CFDR"], "counts": {
            "critical_faults": 8, "detected_critical_faults": 1}}
        self.assertEqual(metrics.calculate(data)["results"]["CFDR"]["ratio"], 0.125)

    def test_cli_rejects_impossible_counts_and_accepts_boundary(self):
        for intersection, expected_code in ((1, 2), (7, 0)):
            with self.subTest(intersection=intersection):
                process = subprocess.run(
                    [sys.executable, str(SCRIPT)],
                    input=json.dumps(assessment(10, 9, 8, intersection)),
                    text=True, capture_output=True, check=False)
                self.assertEqual(process.returncode, expected_code, process.stderr)
                output = json.loads(process.stdout)
                if expected_code:
                    self.assertEqual(output["status"], "invalid_input")
                    self.assertIn("detected_critical_faults", output["error"])
                else:
                    self.assertEqual(output["results"]["CFDR"]["ratio"], 0.875)


if __name__ == "__main__":
    unittest.main()
