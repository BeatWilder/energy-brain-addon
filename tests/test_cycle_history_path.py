from pathlib import Path


def test_history_path():
    path = Path("/data/energy_brain_cycles.jsonl")
    assert path.name == "energy_brain_cycles.jsonl"
    assert path.suffix == ".jsonl"
