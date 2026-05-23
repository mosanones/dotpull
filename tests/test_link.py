"""Unit tests for dotpull.link (low-level symlink helpers)."""

import pytest
from pathlib import Path

from dotpull.link import audit_link, create_link, remove_link, LinkError


@pytest.fixture()
def tmp_source(tmp_path: Path) -> Path:
    src = tmp_path / "dotfiles" / ".bashrc"
    src.parent.mkdir(parents=True)
    src.write_text("# bashrc")
    return src


@pytest.fixture()
def tmp_target(tmp_path: Path) -> Path:
    return tmp_path / "home" / ".bashrc"


def test_create_link_creates_symlink(tmp_source, tmp_target):
    create_link(tmp_source, tmp_target)
    assert tmp_target.is_symlink()
    assert tmp_target.resolve() == tmp_source.resolve()


def test_create_link_creates_parent_dirs(tmp_source, tmp_path):
    target = tmp_path / "home" / "nested" / "dir" / ".bashrc"
    create_link(tmp_source, target)
    assert target.is_symlink()


def test_create_link_raises_if_source_missing(tmp_path):
    with pytest.raises(LinkError, match="Source does not exist"):
        create_link(tmp_path / "nonexistent", tmp_path / "target")


def test_create_link_raises_if_target_exists_no_force(tmp_source, tmp_target):
    tmp_target.parent.mkdir(parents=True)
    tmp_target.write_text("existing")
    with pytest.raises(LinkError, match="already exists"):
        create_link(tmp_source, tmp_target)


def test_create_link_force_overwrites_existing(tmp_source, tmp_target):
    tmp_target.parent.mkdir(parents=True)
    tmp_target.write_text("existing")
    create_link(tmp_source, tmp_target, force=True)
    assert tmp_target.is_symlink()


def test_remove_link_removes_symlink(tmp_source, tmp_target):
    create_link(tmp_source, tmp_target)
    removed = remove_link(tmp_target)
    assert removed is True
    assert not tmp_target.exists()


def test_remove_link_returns_false_for_non_symlink(tmp_path):
    regular = tmp_path / "file.txt"
    regular.write_text("hi")
    assert remove_link(regular) is False


def test_audit_link_ok(tmp_source, tmp_target):
    create_link(tmp_source, tmp_target)
    assert audit_link(tmp_source, tmp_target) == "ok"


def test_audit_link_missing(tmp_source, tmp_target):
    assert audit_link(tmp_source, tmp_target) == "missing"


def test_audit_link_conflict(tmp_source, tmp_target):
    tmp_target.parent.mkdir(parents=True)
    tmp_target.write_text("not a symlink")
    assert audit_link(tmp_source, tmp_target) == "conflict"


def test_audit_link_wrong(tmp_source, tmp_path):
    other_source = tmp_path / "other.txt"
    other_source.write_text("other")
    target = tmp_path / "home" / ".bashrc"
    target.parent.mkdir(parents=True)
    target.symlink_to(other_source)
    assert audit_link(tmp_source, target) == "wrong"
