#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
from tqdm import tqdm

# =========================
# Utils
# =========================

DOC_EXTS = {".md", ".mdx", ".rst", ".adoc", ".asciidoc", ".xml", ".tex", ".html", ".htm"}

def run(cmd: List[str], cwd: Optional[Path] = None) -> None:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")

def sha1_short(text: str, n: int = 10) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:n]

def slugify(s: str, max_length: int = 80) -> str:
    """Slugify a string and limit its length to avoid filesystem issues.

    Linux filesystems have a 255-character limit for filenames.
    We use 80 chars for each slug component to stay well under the limit.
    """
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = s.strip("-") or "section"

    # Limit length and add ellipsis if truncated
    if len(s) > max_length:
        s = s[:max_length].rstrip("-")

    return s

def now_iso() -> str:
    from datetime import timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

# =========================
# Exclusion intelligente
# =========================

def is_artifact_dir(path: Path, excluded_names: List[str]) -> bool:
    for part in path.parts:
        if part in excluded_names:
            # Si le dossier contient de la doc, on ne l'exclut pas
            candidate = Path(*path.parts[:path.parts.index(part)+1])
            try:
                for f in candidate.rglob("*"):
                    if f.suffix.lower() in DOC_EXTS:
                        return False
            except Exception:
                pass
            return True
    return False

# =========================
# Conversion via Pandoc
# =========================

PANDOC_FORMATS = {
    ".md": None,
    ".mdx": ("markdown", "gfm"),
    ".rst": ("rst", "gfm"),
    ".adoc": ("asciidoc", "gfm"),
    ".asciidoc": ("asciidoc", "gfm"),
    ".xml": ("docbook", "gfm"),
    ".tex": ("latex", "gfm"),
    ".html": ("html", "gfm"),
    ".htm": ("html", "gfm"),
}

def convert_to_md(src: Path, dst: Path) -> bool:
    ext = src.suffix.lower()
    ensure_dir(dst.parent)

    if ext == ".md":
        shutil.copy2(src, dst)
        return True

    if ext not in PANDOC_FORMATS:
        return False

    from_fmt, to_fmt = PANDOC_FORMATS[ext]
    cmd = [
        "pandoc", str(src),
        "-f", from_fmt,
        "-t", to_fmt,
        "--wrap=none",
        "--markdown-headings=atx",
        "-o", str(dst)
    ]
    try:
        # Utiliser subprocess.run avec capture d'erreur
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30  # timeout de 30 secondes par fichier
        )

        # Si pandoc retourne une erreur, on la log mais on continue
        if result.returncode != 0:
            # Ne pas afficher les erreurs "UnresolvedEntityException" pour réduire le bruit
            if "UnresolvedEntityException" not in result.stderr:
                print(f"Warning converting {src.name}: {result.stderr[:200]}")
            return False

        return True
    except subprocess.TimeoutExpired:
        print(f"Timeout converting {src.name}")
        return False
    except Exception as e:
        print(f"Error converting {src.name}: {str(e)[:200]}")
        return False

# =========================
# Nettoyage Markdown
# =========================

def clean_md(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<(script|style)[\s\S]*?</\1>", "", text, flags=re.I)
    text = re.sub(r"\{#.*?\}", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"

# =========================
# Découpage par sections
# =========================

def split_by_headers(md: str, max_level: int):
    header_re = re.compile(rf"^(#{{1,{max_level}}})\s+(.+)$", re.MULTILINE)
    matches = list(header_re.finditer(md))

    if not matches:
        return [{"title": "root", "level": 0, "content": md.strip()}]

    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        chunks.append({
            "title": m.group(2).strip(),
            "level": len(m.group(1)),
            "content": md[start:end].strip()
        })
    return chunks

# =========================
# Git
# =========================

def git_clone_or_pull(url: str, dest: Path) -> None:
    if dest.exists() and (dest / ".git").exists():
        run(["git", "fetch", "--depth=1"], cwd=dest)
        run(["git", "reset", "--hard", "origin/HEAD"], cwd=dest)
    else:
        ensure_dir(dest.parent)
        run(["git", "clone", "--depth=1", url, str(dest)])

def get_git_sha(repo_dir: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_dir)).decode().strip()
    except Exception:
        return ""

# =========================
# YAML front-matter
# =========================

def yaml_front_matter(meta: Dict[str, Any]) -> str:
    return f"---\n{yaml.safe_dump(meta, sort_keys=False)}---\n\n"

# =========================
# Main Builder
# =========================

@dataclass
class RepoConfig:
    id: str
    url: str
    category: str
    tech: str
    versions: List[str]
    source: str = "official"

def main():
    cfg = yaml.safe_load(Path("repos.yaml").read_text())
    output_root = Path(cfg["output_root"])
    work_root = Path(cfg["work_root"])
    defaults = cfg["defaults"]

    excluded_names = defaults["exclude_dirs"]
    max_header_level = defaults["max_header_level"]

    ensure_dir(output_root)
    ensure_dir(work_root)

    for r in cfg["repos"]:
        repo = RepoConfig(**r)

        for version in repo.versions:
            print(f"\n### Processing {repo.id} (version: {version})")

            repo_dir = work_root / repo.id
            git_clone_or_pull(repo.url, repo_dir)
            sha = get_git_sha(repo_dir)

            # Output directory preserving GitHub structure
            base_out = output_root / repo.category / repo.tech / version
            ensure_dir(base_out)

            manifest = base_out / "manifest.jsonl"
            mf = manifest.open("w", encoding="utf-8")

            files = []
            for f in repo_dir.rglob("*"):
                if not f.is_file():
                    continue
                if is_artifact_dir(f, excluded_names):
                    continue
                if f.suffix.lower() in DOC_EXTS:
                    files.append(f)

            for src in tqdm(files, desc=f"{repo.id}/{version}"):
                rel = src.relative_to(repo_dir)
                # Preserve exact GitHub structure in output
                dst = base_out / rel.with_suffix(".md")
                ok = convert_to_md(src, dst)
                if not ok:
                    continue

                md = clean_md(dst.read_text(encoding="utf-8", errors="ignore"))
                dst.write_text(md, encoding="utf-8")

                # Add metadata to manifest
                meta = {
                    "repo": repo.id,
                    "tech": repo.tech,
                    "version": version,
                    "source": repo.source,
                    "git_sha": sha,
                    "file_path": str(rel.with_suffix(".md")),
                    "original_file": str(rel),
                    "generated_at": now_iso()
                }

                mf.write(json.dumps({
                    "id": f"{repo.id}:{version}:{sha1_short(str(rel))}",
                    "file": str(rel.with_suffix(".md")),
                    "text": md,
                    **meta
                }, ensure_ascii=False) + "\n")

            mf.close()

    print("\n✅ Corpus LLM prêt :", output_root.resolve())

if __name__ == "__main__":
    main()
