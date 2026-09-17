import json
from importlib import resources

import pytest
from trace_semantics.demo import main


def _bundled_fixture_dir():
    return resources.files("trace_semantics").joinpath("fixtures", "demo")


def _read_bundled(name):
    return json.loads(_bundled_fixture_dir().joinpath(name).read_text(encoding="utf-8"))


def test_demo_default_and_explicit_fixture_write_exact_raw_artifacts(tmp_path):
    expected = _read_bundled("expected.json")
    with resources.as_file(_bundled_fixture_dir()) as fixture_dir:
        default_out = tmp_path / "default"
        explicit_out = tmp_path / "explicit"
        main(["--out", str(default_out)])
        main(["--fixture-dir", str(fixture_dir), "--out", str(explicit_out)])

    for output_dir in (default_out, explicit_out):
        assert json.loads((output_dir / "summary.json").read_text(encoding="utf-8")) == expected
        description = json.loads((output_dir / "description.json").read_text(encoding="utf-8"))
        partition = json.loads((output_dir / "partition.json").read_text(encoding="utf-8"))
        deferred = json.loads((output_dir / "deferred.json").read_text(encoding="utf-8"))
        assert deferred == partition["deferred"]
        traces = _read_bundled("traces.json")
        assert [trace["raw"] for trace in description["traces"]] == traces
        assert {path.name for path in output_dir.iterdir()} == {
            "partition.json", "deferred.json", "description.json", "summary.json"
        }


def test_demo_rejects_edited_expected_before_creating_output(tmp_path):
    fixture_dir = tmp_path / "fixture"
    fixture_dir.mkdir()
    with resources.as_file(_bundled_fixture_dir()) as bundled:
        for name in ("traces.json", "policy.json", "expected.json"):
            (fixture_dir / name).write_text(
                bundled.joinpath(name).read_text(encoding="utf-8"), encoding="utf-8"
            )
    expected = json.loads((fixture_dir / "expected.json").read_text(encoding="utf-8"))
    expected["selected_traces"] += 1
    (fixture_dir / "expected.json").write_text(json.dumps(expected), encoding="utf-8")

    with pytest.raises(ValueError, match="expected summary mismatch"):
        main(["--fixture-dir", str(fixture_dir), "--out", str(tmp_path / "rejected")])
    assert not (tmp_path / "rejected").exists()


def test_demo_refuses_to_overwrite_existing_output_directory(tmp_path):
    output_dir = tmp_path / "existing"
    output_dir.mkdir()
    marker = output_dir / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="output directory already exists"):
        main(["--out", str(output_dir)])
    assert marker.read_text(encoding="utf-8") == "keep"
