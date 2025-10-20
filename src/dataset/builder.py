from __future__ import annotations

import json
from typing import Iterable, List, Tuple

from src.services.base import LLMService


def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
	chunks: List[str] = []
	current: List[str] = []
	current_len = 0
	for line in text.splitlines():
		line = line.strip()
		if not line:
			continue
		if current_len + len(line) + 1 > max_chars:
			if current:
				chunks.append("\n".join(current))
				current = []
				current_len = 0
		current.append(line)
		current_len += len(line) + 1
	if current:
		chunks.append("\n".join(current))
	return chunks


class DatasetBuilder:
	def __init__(self, llm: LLMService) -> None:
		self._llm = llm

	def build_qa_jsonl(self, docs: Iterable[Tuple[str, str]], *, num_pairs_per_chunk: int = 3,
					  model: str | None = None, user_prompt: str | None = None) -> List[dict]:
		records: List[dict] = []
		for _path, text in docs:
			for chunk in chunk_text(text):
				# If a custom prompt is provided, use it literally with the chunk injected at the end.
				if user_prompt:
					pairs = self._llm.synthesize_qa_pairs(
						f"{user_prompt}\n\nTEXT:\n{chunk}", model=model, num_pairs=num_pairs_per_chunk
					)
				else:
					pairs = self._llm.synthesize_qa_pairs(chunk, model=model, num_pairs=num_pairs_per_chunk)
				for pair in pairs:
					records.append({
						"input": pair["input"],
						"output": pair["output"],
					})
		return records

	@staticmethod
	def save_jsonl(records: List[dict], out_path: str) -> None:
		with open(out_path, "w", encoding="utf-8") as f:
			for rec in records:
				f.write(json.dumps(rec, ensure_ascii=False) + "\n")
