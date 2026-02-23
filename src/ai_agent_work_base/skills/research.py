import os
from typing import Any, Dict
from dotenv import load_dotenv
from tavily import TavilyClient
from .base import BaseSkill

load_dotenv()


class WebSearchSkill(BaseSkill):
    """
    Tavily APIを使用してWeb検索を行うスキル。
    TAVILY_API_KEY環境変数が必要。
    """

    def __init__(self):
        """Tavily APIクライアントを初期化する。"""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY が設定されていません。.envファイルに追加してください。")
        self._client = TavilyClient(api_key=api_key)

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "指定されたクエリでWeb検索を行い、結果のサマリーを返します。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query."
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str, **kwargs) -> str:
        """Web検索を実行し、結果を文字列で返す。TavilyがNG時はDuckDuckGoにフォールバック。"""
        try:
            response = self._client.search(query=query, max_results=5)
            results = response.get("results", [])
            if not results:
                return f"'{query}' の検索結果が見つかりませんでした。"
            lines = [f"## 検索クエリ: {query}\n"]
            for i, r in enumerate(results, 1):
                title = r.get("title", "タイトルなし")
                url = r.get("url", "")
                content = r.get("content", "").strip()
                lines.append(f"{i}. **{title}**\n   URL: {url}\n   {content}\n")
            return "\n".join(lines)
        except Exception:
            return self._search_duckduckgo(query)

    def _search_duckduckgo(self, query: str) -> str:
        """DuckDuckGoで検索する（APIキー不要・フォールバック用）。"""
        from duckduckgo_search import DDGS
        results = list(DDGS().text(query, max_results=5))
        if not results:
            return f"'{query}' の検索結果が見つかりませんでした。"
        lines = [f"## 検索クエリ: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "タイトルなし")
            url = r.get("href", "")
            content = r.get("body", "").strip()
            lines.append(f"{i}. **{title}**\n   URL: {url}\n   {content}\n")
        return "\n".join(lines)
