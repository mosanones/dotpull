"""Tests for dotpull.export."""

import json
import tarfile
from pathlib import Path

import pytest

from dotpull.export import export_profile, import_archive, ExportError
from dotpull.profile import Profile


@pytest.fixture()
def dotfiles_dir(tmp_path):
    d = tmp_path / "dotfiles"
    d.mkdir()
    (d / "bashrc").write_text("export PATH=~/bin:$PATH\n")
    (d / "vimrc").write_text('set number\n')
    return d


@pytest.fixture()
def simple_profile(dotfiles_dir):
    return Profile(name="default", files=["bashrc", "vimrc"], variables={})


@pytest.fixture()
def output_dir(tmp_path):
    return tmp_path / "exports"


def test_export_creates_archive(dotfiles_dir, simple_profile, output_dir):
    archive = export_profile(simple_profile, dotfiles_dir, output_dir)
    assert archive.exists()
    assert archive.suffix == ".gz"


def test_export_archive_contains_files(dotfiles_dir, simple_profile, output_dir):
    archive = export_profile(simple_profile, dotfiles_dir, output_dir)
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
    assert "bashrc" in names
    assert "vimrc" in names


def test_export_archive_contains_manifest(dotfiles_dir, simple_profile, output_dir):
    archive = export_profile(simple_profile, dotfiles_dir, output_dir)
    with tarfile.open(archive, "r:gz") as tar:
        assert "manifest.json" in tar.getnames()
        f = tar.extractfile("manifest.json")
        manifest = json.loads(f.read())
    assert manifest["profile"] == "default"
    assert len(manifest["files"]) == 2
    assert all("sha256" in entry for entry in manifest["files"])


def test_export_with_label(dotfiles_dir, simple_profile, output_dir):
    archive = export_profile(simple_profile, dotfiles_dir, output_dir, label="v1")
    assert "v1" in archive.name


def test_export_raises_on_missing_dotfiles_dir(simple_profile, tmp_path):
    with pytest.raises(ExportError, match="dotfiles directory not found"):
        export_profile(simple_profile, tmp_path / "nope", tmp_path / "out")


def test_export_raises_on_missing_file(dotfiles_dir, output_dir):
    profile = Profile(name="p", files=["missing_file"], variables={})
    with pytest.raises(ExportError, match="source file missing"):
        export_profile(profile, dotfiles_dir, output_dir)


def test_import_restores_files(dotfiles_dir, simple_profile, output_dir, tmp_path):
    archive = export_profile(simple_profile, dotfiles_dir, output_dir)
    restore_dir = tmp_path / "restored"
    restored = import_archive(archive, restore_dir)
    assert set(restored) == {"bashrc", "vimrc"}
    assert (restore_dir / "bashrc").exists()


def test_import_raises_on_missing_archive(tmp_path):
    with pytest.raises(ExportError, match="archive not found"):
        import_archive(tmp_path / "ghost.tar.gz", tmp_path / "out")
