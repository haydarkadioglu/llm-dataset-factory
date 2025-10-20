from __future__ import annotations

from typing import Protocol, List, Dict, Optional


class LLMService(Protocol):
	def generate(self, *, system_prompt: str, user_prompt: str, model: Optional[str] = None,
				temperature: float = 0.2, max_tokens: int = 1024, retries: int = 3,
				timeout: int = 60) -> str:  # pragma: no cover
		...

	def synthesize_qa_pairs(self, text_chunk: str, *, model: Optional[str] = None,
							num_pairs: int = 3) -> List[Dict[str, str]]:  # pragma: no cover
		...
