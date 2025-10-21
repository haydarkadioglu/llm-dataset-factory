from __future__ import annotations

import os
import json
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


def read_ipynb_file(path: str) -> str:
	try:
		with open(path, "r", encoding="utf-8", errors="ignore") as f:
			data = json.load(f)
	except Exception:
		return ""
	cells = data.get("cells", []) if isinstance(data, dict) else []
	parts: List[str] = []
	for cell in cells:
		cell_type = cell.get("cell_type")
		source = cell.get("source", [])
		if isinstance(source, list):
			text = "".join(source)
		else:
			text = str(source or "")
		if not text.strip():
			continue
		if cell_type == "markdown":
			parts.append(text.strip())
		elif cell_type == "code":
			# Prefix with a tag to preserve context
			parts.append(f"```code\n{text.strip()}\n```")
	return "\n\n".join(parts)


def load_documents(paths: Iterable[str]) -> List[tuple[str, str]]:
	"""Return list of (path, text). Supports .txt, .md, .pdf, .py, .cpp, .ipynb, .bat, .sh"""
	results: List[tuple[str, str]] = []
	for path in paths:
		ext = os.path.splitext(path)[1].lower()
		if ext in (".txt", ".md", ".py", ".cpp", ".bat", ".sh"):
			content = read_text_file(path)
		elif ext == ".pdf":
			content = read_pdf_file(path)
		elif ext == ".ipynb":
			content = read_ipynb_file(path)
		else:
			# Skip unsupported
			continue
		if content.strip():
			results.append((path, content))
	return results
