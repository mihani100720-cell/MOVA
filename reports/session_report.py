"""
MOVA Session Report: Aggregates and formats completed session data
"""

from typing import Dict, Any, List
from reports.pdf_report import PDFReportGenerator
from database.repository import repo

class SessionReportService:
    @classmethod
    def compile_session_report(cls, session_id: str) -> Dict[str, Any]:
        results = repo.get_recent_results(limit=10)
        matching = [r for r in results if r.get("session_id") == session_id]
        if not matching:
            matching = results[:1] if results else []

        last = matching[0] if matching else {}
        trend = repo.get_comparison_trend("default_user", last.get("game_id", "galaxy_rescue"), last) if last else {}

        return {
            "session_id": session_id,
            "results": matching,
            "trend": trend
        }

    @classmethod
    def export_pdf(cls, session_metadata: Dict[str, Any],
                   game_results: List[Dict[str, Any]],
                   trend_analysis: Dict[str, Any],
                   coach_text: str) -> bytes:
        return PDFReportGenerator.generate_pdf(session_metadata, game_results, trend_analysis, coach_text)
