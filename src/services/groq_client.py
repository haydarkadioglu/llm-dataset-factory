from __future__ import annotations

import json
import time
from typing import List, Dict, Optional

import requests

from src.config import AppConfig


class GroqService:
	"""Thin wrapper around Groq Chat Completions API.

	Uses HTTP via requests to avoid tight coupling to a specific SDK version.
	"""

	_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

	def __init__(self, config: AppConfig) -> None:
		self._config = config

	def generate(self, *, system_prompt: str, user_prompt: str, model: Optional[str] = None,
				temperature: float = 0.2, max_tokens: int = 1024, retries: int = 3,
				timeout: int = 60) -> str:
		payload = {
			"model": model or self._config.default_model,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			"temperature": temperature,
			"max_tokens": max_tokens,
		}
		headers = {
			"Authorization": f"Bearer {self._config.groq_api_key}",
			"Content-Type": "application/json",
		}

		last_error: Optional[Exception] = None
		for attempt in range(retries + 1):
			try:
				resp = requests.post(self._BASE_URL, headers=headers, data=json.dumps(payload), timeout=timeout)
				if resp.status_code == 200:
					data = resp.json()
					return data["choices"][0]["message"]["content"].strip()
				# Retry for 429/5xx
				if resp.status_code in (429, 500, 502, 503, 504):
					last_error = RuntimeError(f"Groq API error {resp.status_code}: {resp.text[:200]}")
					time.sleep(min(2 ** attempt, 10))
					continue
				# Non-retryable
				resp.raise_for_status()
			except Exception as exc:
				last_error = exc
				time.sleep(min(2 ** attempt, 10))
		raise RuntimeError(f"Groq generate failed after retries: {last_error}")

	def synthesize_qa_pairs(self, text_chunk: str, *, model: Optional[str] = None,
							num_pairs: int = 3) -> List[Dict[str, str]]:
		system_prompt = (
			"You create high-quality question-answer pairs for supervised fine-tuning. "
			"Keep questions grounded only in the provided text, avoid outside knowledge. "
			"Answers must be concise but complete."
		)
		user_prompt = (
			f"From the following text, write {num_pairs} diverse question-answer pairs.\n\n"
			f"Text:\n{text_chunk}\n\n"
			"Return JSON array with objects having 'input' and 'output' keys only."
		)
		result = self.generate(system_prompt=system_prompt, user_prompt=user_prompt, model=model)
		try:
			parsed = json.loads(self._extract_json(result))
			cleaned: List[Dict[str, str]] = []
			for item in parsed:
				inp = str(item.get("input", "")).strip()
				out = str(item.get("output", "")).strip()
				if inp and out:
					cleaned.append({"input": inp, "output": out})
			return cleaned
		except Exception:
			# Fallback: wrap as a single pair if JSON parsing fails
			return [{"input": "Summarize the text:", "output": result}]

	@staticmethod
	def _extract_json(text: str) -> str:
		start = text.find("[")
		end = text.rfind("]")
		if start != -1 and end != -1 and end > start:
			return text[start:end + 1]
		return text
