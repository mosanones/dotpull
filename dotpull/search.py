"""Search dotfiles and profiles by file path, tag, or variable name."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotpull.profile import Profile


@dataclass
class SearchResult:
    profile_name: str
    matched_files: List[str] = field(default_factory=list)
    matched_variables: List[str] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return bool(self.matched_files or self.matched_variables)


def search_profiles(
    profiles: dict[str, Profile],
    query: str,
    *,
    search_files: bool = True,
    search_variables: bool = True,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Search across all profiles for files or variables matching *query*."""
    needle = query if case_sensitive else query.lower()
    results: List[SearchResult] = []

    for name, profile in profiles.items():
        result = SearchResult(profile_name=name)

        if search_files:
            for src, _dst in (profile.files or {}).items():
                haystack = src if case_sensitive else src.lower()
                if needle in haystack:
                    result.matched_files.append(src)

        if search_variables:
            for var_key in (profile.variables or {}):
                haystack = var_key if case_sensitive else var_key.lower()
                if needle in haystack:
                    result.matched_variables.append(var_key)

        if result.has_matches:
            results.append(result)

    return results


def search_files_by_extension(
    profiles: dict[str, Profile],
    extension: str,
) -> List[SearchResult]:
    """Return profiles that manage at least one file with *extension*."""
    ext = extension.lstrip(".")
    results: List[SearchResult] = []

    for name, profile in profiles.items():
        matched = [
            src
            for src in (profile.files or {})
            if Path(src).suffix.lstrip(".") == ext
        ]
        if matched:
            results.append(SearchResult(profile_name=name, matched_files=matched))

    return results
