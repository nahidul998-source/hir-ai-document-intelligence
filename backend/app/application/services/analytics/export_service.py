import io
import csv
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ReportExportService:
    """
    Export Engine supporting CSV, Excel-compatible XML/TSV, and PDF report formats.
    """
    @staticmethod
    def generate_csv_report(data: List[Dict[str, Any]]) -> str:
        """Generates raw CSV formatted string stream."""
        if not data:
            return "metric_name,value\n"
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def generate_excel_report(data: List[Dict[str, Any]], title: str = "BI Analytics Report") -> str:
        """Generates Excel-compatible HTML/XML spreadsheet content."""
        headers = list(data[0].keys()) if data else ["Metric", "Value"]
        rows_html = ""
        for item in data:
            cells = "".join([f"<td>{v}</td>" for v in item.values()])
            rows_html += f"<tr>{cells}</tr>"

        headers_html = "".join([f"<th>{h}</th>" for h in headers])
        
        excel_content = f"""
        <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
        <head><meta charset="utf-8"/><title>{title}</title></head>
        <body>
        <h2>HIR Platform — {title}</h2>
        <table border="1">
            <thead><tr>{headers_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        </body>
        </html>
        """
        return excel_content.strip()

    @staticmethod
    def generate_pdf_report(summary: Dict[str, Any]) -> str:
        """Generates a text/HTML printable PDF format stream."""
        return f"""
        === HIR PLATFORM EXECUTIVE BI REPORT ===
        Total Documents Processed: {summary.get('total_documents', 0)}
        Overall AI Accuracy: {summary.get('ai_accuracy_pct', 0)}%
        ERP Success Rate: {summary.get('erp_success_rate_pct', 0)}%
        SLA Compliance Rate: {summary.get('sla_compliance_pct', 0)}%
        Total AI Tokens Consumed: {summary.get('total_tokens_consumed', 0)}
        Estimated AI Cost: ${summary.get('estimated_ai_cost_usd', 0.0)} USD
        ========================================
        """.strip()
