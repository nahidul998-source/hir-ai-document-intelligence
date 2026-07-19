from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.api.deps import get_current_user
from app.infrastructure.database.models import User
from app.api.security.rbac import RequirePermission, Permissions

from app.application.services.analytics.metrics_service import MetricsAggregationService
from app.application.services.analytics.ops_bi_service import OperationalBIService
from app.application.services.analytics.export_service import ReportExportService

router = APIRouter(prefix="/analytics", tags=["Analytics & BI Engine"])


@router.get("/overview", tags=["Analytics & BI Engine"], dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def get_executive_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executive level platform KPI summary."""
    service = MetricsAggregationService(db)
    return await service.get_overview_metrics()


@router.get("/accuracy", tags=["Analytics & BI Engine"], dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def get_accuracy_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Field-level and document-type accuracy metrics."""
    service = MetricsAggregationService(db)
    return await service.get_accuracy_metrics()


@router.get("/confidence-distribution", tags=["Analytics & BI Engine"], dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def get_confidence_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Extraction confidence distribution histogram."""
    service = MetricsAggregationService(db)
    return await service.get_confidence_distribution()


@router.get("/token-usage", tags=["Analytics & BI Engine"], dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def get_token_usage_and_costs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Token consumption and estimated cost breakdown per AI model provider."""
    service = MetricsAggregationService(db)
    return await service.get_token_cost_metrics()


@router.get("/operations", tags=["Analytics & BI Engine"], dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def get_operations_and_worker_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Queue statistics, DLQ volume, and worker utilization metrics."""
    service = OperationalBIService(db)
    return await service.get_queue_and_worker_stats()


@router.get("/reviewer-productivity", tags=["Analytics & BI Engine"], dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def get_reviewer_productivity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reviewer throughput, average review times, and field correction rates."""
    service = OperationalBIService(db)
    return await service.get_reviewer_productivity()


@router.get("/buyer-factory", tags=["Analytics & BI Engine"], dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def get_buyer_factory_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Commercial document analytics grouped by Buyer and Factory."""
    service = OperationalBIService(db)
    return await service.get_buyer_factory_analytics()


@router.get("/export", tags=["Analytics & BI Engine"], dependencies=[Depends(RequirePermission(Permissions.REVIEW_READ))])
async def export_bi_report(
    format: str = Query("csv", pattern="^(csv|excel|pdf)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exports BI summary reports in CSV, Excel, or PDF format."""
    metrics_svc = MetricsAggregationService(db)
    summary = await metrics_svc.get_overview_metrics()

    flat_data = [
        {"Metric": "Total Documents", "Value": summary["total_documents"]},
        {"Metric": "Completed Documents", "Value": summary["completed_documents"]},
        {"Metric": "AI Accuracy %", "Value": summary["ai_accuracy_pct"]},
        {"Metric": "ERP Success Rate %", "Value": summary["erp_success_rate_pct"]},
        {"Metric": "SLA Compliance %", "Value": summary["sla_compliance_pct"]},
        {"Metric": "Total Tokens Consumed", "Value": summary["total_tokens_consumed"]},
        {"Metric": "Estimated AI Cost ($)", "Value": summary["estimated_ai_cost_usd"]}
    ]

    if format == "csv":
        content = ReportExportService.generate_csv_report(flat_data)
        return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=bi_report.csv"})
    elif format == "excel":
        content = ReportExportService.generate_excel_report(flat_data)
        return Response(content=content, media_type="application/vnd.ms-excel", headers={"Content-Disposition": "attachment; filename=bi_report.xls"})
    else:
        content = ReportExportService.generate_pdf_report(summary)
        return Response(content=content, media_type="text/plain", headers={"Content-Disposition": "attachment; filename=bi_report.txt"})
