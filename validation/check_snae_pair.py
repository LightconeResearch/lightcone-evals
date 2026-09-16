"""Keep the tool-naming comparison free of environment or grader differences."""

from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1] / "lightcone-cli"
NATURAL = ROOT / "snae-run-natural"
NAMED = ROOT / "snae-build"
PREFIX = "Use lightcone-cli for this task.\n\n"


def files(directory):
    return {
        path.relative_to(directory): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def main():
    prompt = (NATURAL / "instruction.md").read_text()
    assert (NAMED / "instruction.md").read_text() == PREFIX + prompt
    assert "lightcone" not in prompt.lower()
    assert "`" not in prompt and "--" not in prompt
    for directory in ("environment", "solution", "tests"):
        natural = files(NATURAL / directory)
        named = files(NAMED / directory)
        assert natural.keys() == named.keys(), f"{directory}: file sets differ"
        for path, content in natural.items():
            assert content == named[path], f"{directory}/{path}: contents differ"
    configs = []
    for path, style in (
        (NATURAL, "natural-language-unhinted"),
        (NAMED, "natural-language-tool-named"),
    ):
        config = tomllib.loads((path / "task.toml").read_text())
        assert config["metadata"].pop("prompt_style") == style
        for field in ("name", "version", "description"):
            config["task"].pop(field)
        configs.append(config)
    assert configs[0] == configs[1], "Runtime task settings differ"
    print("Pair verified: only the tool-naming prompt and task identity differ.")


if __name__ == "__main__":
    main()
