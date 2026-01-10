#!/usr/bin/env python3
"""Check which assets are referenced in markdown files."""

import os
import re
from pathlib import Path


def find_all_assets(assets_dir: Path) -> list[Path]:
  """Find all files under the assets directory."""
  assets = []
  for root, _, files in os.walk(assets_dir):
    for file in files:
      assets.append(Path(root) / file)
  return assets


def find_all_md_files(root_dir: Path) -> list[Path]:
  """Find all markdown files in the project."""
  md_files = []
  for file in root_dir.glob("*.md"):
    md_files.append(file)
  return md_files


def find_all_liquid_files(root_dir: Path) -> list[Path]:
  """Find all liquid template files."""
  liquid_files = []
  for pattern in ["_includes/**/*.liquid", "_layouts/**/*.liquid"]:
    liquid_files.extend(root_dir.glob(pattern))
  return liquid_files


def find_all_scss_files(root_dir: Path) -> list[Path]:
  """Find all SCSS files."""
  return list(root_dir.glob("_sass/**/*.scss"))


def check_asset_usage(
    asset: Path,
    md_files: list[Path],
    liquid_files: list[Path],
    scss_files: list[Path],
    assets_dir: Path,
) -> dict[str, list[str]]:
  """Check if an asset is referenced in any source file."""
  relative_path = asset.relative_to(assets_dir.parent)
  filename = asset.name
  stem = asset.stem

  # Patterns to search for
  patterns = [
    str(relative_path),  # Full path: assets/img/foo.png
    f"/{relative_path}",  # With leading slash
    filename,  # Just filename
  ]

  # For images, also check without extension (responsive images)
  if asset.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]:
    patterns.append(stem)

  references: dict[str, list[str]] = {"md": [], "liquid": [], "scss": []}

  for md_file in md_files:
    content = md_file.read_text(errors="ignore")
    for pattern in patterns:
      if pattern in content:
        references["md"].append(str(md_file.name))
        break

  for liquid_file in liquid_files:
    content = liquid_file.read_text(errors="ignore")
    for pattern in patterns:
      if pattern in content:
        references["liquid"].append(str(liquid_file.relative_to(liquid_file.parent.parent)))
        break

  for scss_file in scss_files:
    content = scss_file.read_text(errors="ignore")
    for pattern in patterns:
      if pattern in content:
        references["scss"].append(str(scss_file.relative_to(scss_file.parent.parent)))
        break

  return references


def main():
  root_dir = Path(__file__).parent
  assets_dir = root_dir / "assets"

  print("Scanning for assets and references...\n")

  assets = find_all_assets(assets_dir)
  md_files = find_all_md_files(root_dir)
  liquid_files = find_all_liquid_files(root_dir)
  scss_files = find_all_scss_files(root_dir)

  print(f"Found {len(assets)} assets")
  print(f"Found {len(md_files)} markdown files")
  print(f"Found {len(liquid_files)} liquid templates")
  print(f"Found {len(scss_files)} scss files\n")

  used_assets: list[tuple[Path, dict]] = []
  unused_assets: list[Path] = []

  for asset in sorted(assets):
    refs = check_asset_usage(asset, md_files, liquid_files, scss_files, assets_dir)
    has_refs = any(refs.values())

    if has_refs:
      used_assets.append((asset, refs))
    else:
      unused_assets.append(asset)

  print("=" * 60)
  print("USED ASSETS")
  print("=" * 60)
  for asset, refs in used_assets:
    rel_path = asset.relative_to(assets_dir)
    ref_summary = []
    if refs["md"]:
      ref_summary.append(f"md: {', '.join(refs['md'][:3])}")
    if refs["liquid"]:
      ref_summary.append(f"liquid: {', '.join(refs['liquid'][:3])}")
    if refs["scss"]:
      ref_summary.append(f"scss: {', '.join(refs['scss'][:3])}")
    print(f"  {rel_path}")
    print(f"    -> {'; '.join(ref_summary)}")

  print("\n" + "=" * 60)
  print("UNUSED ASSETS (not referenced anywhere)")
  print("=" * 60)
  total_size = 0
  for asset in unused_assets:
    rel_path = asset.relative_to(assets_dir)
    size = asset.stat().st_size
    total_size += size
    print(f"  {rel_path} ({size:,} bytes)")

  print(f"\nTotal unused: {len(unused_assets)} files, {total_size:,} bytes")
  print(f"Total used: {len(used_assets)} files")


if __name__ == "__main__":
  main()
