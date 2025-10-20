from __future__ import annotations

import os
from typing import Iterable, List

import pdfplumber


def read_text_file(path: str) -> str:
	with open(path, "r", encoding="utf-8", errors="ignore") as f:
		return f.read()


def read_pdf_file(path: str) -> str:
	parts: List[str] = []
	with pdfplumber.open(path) as pdf:
		for page in pdf.pages:
			text = page.extract_text() or ""
			parts.append(text)
	return "\n".join(parts)


def load_documents(paths: Iterable[str]) -> List[tuple[str, str]]:
	"""Return list of (path, text). Supports .txt, .md, .pdf"""
	results: List[tuple[str, str]] = []
	for path in paths:
		ext = os.path.splitext(path)[1].lower()
		if ext in (".txt", ".md"):
			content = read_text_file(path)
		elif ext == ".pdf":
			content = read_pdf_file(path)
		else:
			# Skip unsupported
			continue
		if content.strip():
			results.append((path, content))
	return results
