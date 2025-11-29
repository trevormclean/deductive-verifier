import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ROOT))

from lexer import Lexer
from parser import Parser
from verifier import check_verification

PROGRAM_DIR = Path(__file__).parent / "programs"

TEST_CASES = [
    ("assign_ok.txt", True),
    ("assign_fail.txt", False),

    ("seq_two_assign_ok.txt", True),
    ("seq_two_assign_fail.txt", False),

    ("if_ok_abs.txt", True),
    ("if_fail_abs.txt", False),
    ("nested_if_ok.txt", True),
    ("nested_if_fail.txt", False),
    ("if_bool_ok.txt", True),
    ("if_bool_fail.txt", False),

    ("while_ok_counter.txt", True),
    ("while_weak_invariant.txt", False),
    ("while_bad_invariant_preserve.txt", False),
    ("while_skip_ok.txt", True),
    ("while_pre_not_implies_invariant.txt", False),
    ("bool_invariant_ok.txt", True),

    ("implication_logic_ok.txt", True),

    ("trivial_true.txt", True),
    ("trivial_false_post.txt", False),
    ("unsat_precondition.txt", True),

    ("comments_ok.txt", True)
]


def run_program_file(path: Path):
    """
    Run the full pipeline on one program file
    """
    text = path.read_text()
    tokens = Lexer(text).tokenize()
    parser = Parser(tokens)
    program = parser.parse_program()
    ok, model = check_verification(program)
    return ok, model


@pytest.mark.parametrize("filename, expected_ok", TEST_CASES)
def test_verifier_on_programs(filename, expected_ok):
    path = PROGRAM_DIR / filename
    assert path.exists(), f"Missing test program file: {path}"

    ok, model = run_program_file(path)

    if expected_ok:
        assert ok, (
            f"Expected '{filename}' to be VERIFIED, but it was NOT.\n"
            f"Counterexample model (if any): {model}"
        )
    else:
        assert not ok, (
            f"Expected '{filename}' to FAIL verification, but it was VERIFIED.\n"
            f"(No counterexample returned; check your wp rules / VCs.)"
        )

    if not expected_ok:
        assert model is not None, (
            f"Expected a counterexample model for failing program '{filename}', "
            f"but model was None."
        )