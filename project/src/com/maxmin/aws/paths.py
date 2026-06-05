from pathlib import Path
import os


def get_repo_root() -> Path:
    """Return the repository root by searching upward for the directory that contains the
    top-level `project` directory. Fall back to `DATACENTER_DIR` env var or parent chain."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "project").is_dir():
            return parent

    env = os.getenv("DATACENTER_DIR")
    if env:
        return Path(env)

    # As a final fallback return the repository two levels up from this module
    return current.parents[5]


def project_subdir(*parts) -> Path:
    """Return a path under the repository root, e.g. project_subdir('config')."""
    return get_repo_root().joinpath(*parts)
