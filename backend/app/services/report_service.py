"""Report generation (PDF) - incident, daily, weekly, zone and risk reports."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models import Alert, Hotspot, IndustrialZone
from app.utils.helpers import risk_level_for

NAVY = colors.HexColor("#0b1220")
RED = colors.HexColor("#ef4444")
ORANGE = colors.HexColor("#f97316")
BLUE = colors.HexColor("#3b82f6")
GRAY = colors.HexColor("#64748b")


def _styles():
    s = getSampleStyleSheet()
    title = ParagraphStyle("FireXTitle", parent=s["Title"], fontSize=20, textColor=NAVY, spaceAfter=2)
    subtitle = ParagraphStyle("FireXSub", parent=s["Normal"], fontSize=9, textColor=GRAY, alignment=TA_CENTER)
    h2 = ParagraphStyle("FireXH2", parent=s["Heading2"], fontSize=12, textColor=NAVY, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("FireXBody", parent=s["Normal"], fontSize=9, leading=13)
    small = ParagraphStyle("FireXSmall", parent=s["Normal"], fontSize=8, leading=11, textColor=GRAY)
    return title, subtitle, h2, body, small


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, doc.pagesize[1] - 12 * mm, doc.pagesize[0], 12 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(16 * mm, doc.pagesize[1] - 8 * mm, "FIRE-X")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(doc.pagesize[0] - 16 * mm, doc.pagesize[1] - 8 * mm, "Fire Intelligence & Risk Evaluation Platform")
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(16 * mm, 10 * mm, f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} - CONFIDENTIAL")
    canvas.drawRightString(doc.pagesize[0] - 16 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _kv_table(rows: list[tuple[str, str]]) -> Table:
    t = Table([[Paragraph(k, _styles()[4]), Paragraph(v, _styles()[3])] for k, v in rows], colWidths=[50 * mm, 130 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _classification_color(cls: str) -> str:
    mapping = {
        "Industrial Fire": "#ef4444",
        "Wildfire": "#f97316",
        "Agricultural Burning": "#eab308",
        "Gas Flare": "#a855f7",
        "Persistent Industrial Heat Source": "#3b82f6",
        "Other Thermal Anomaly": "#64748b",
    }
    return mapping.get(cls, "#64748b")


def build_incident_report(db: Session, hotspot: Hotspot) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=22 * mm, bottomMargin=16 * mm)
    title, subtitle, h2, body, small = _styles()
    story = [
        Paragraph("FIRE-X", title),
        Paragraph("Fire Intelligence &amp; Risk Evaluation Platform - Incident Report", subtitle),
        Spacer(1, 4),
        Paragraph(f"Incident ID: {hotspot.code} | Classification: {hotspot.classification}", subtitle),
        Spacer(1, 8),
    ]

    story.append(Paragraph("1. Detection Summary", h2))
    ftr = hotspot.features
    story.append(
        _kv_table(
            [
                ("Hotspot ID", hotspot.code),
                ("Latitude / Longitude", f"{hotspot.latitude:.5f} / {hotspot.longitude:.5f}"),
                ("Acquisition", hotspot.acquisition_time.strftime("%Y-%m-%d %H:%M UTC") if hotspot.acquisition_time else "-"),
                ("Satellite / Sensor", hotspot.satellite),
                ("Brightness temperature", f"{hotspot.brightness:.1f} K"),
                ("FRP", f"{hotspot.frp:.2f} MW"),
                ("Confidence", f"{hotspot.confidence * 100:.0f}%"),
                ("State / District", f"{hotspot.state} / {hotspot.district}"),
                ("Land cover", hotspot.land_cover),
            ]
        )
    )

    story.append(Paragraph("2. AI Classification & Risk", h2))
    story.append(
        _kv_table(
            [
                ("Classification", hotspot.classification),
                ("Classification confidence", f"{hotspot.classification_confidence * 100:.1f}%"),
                ("Risk score", f"{hotspot.risk_score:.0f} / 100 ({hotspot.risk_level})"),
                ("Persistence score", f"{hotspot.persistence_score:.0f}"),
                ("Temporal pattern", hotspot.temporal_pattern),
                ("Recommended action", _action_for(hotspot.risk_level)),
            ]
        )
    )

    story.append(Paragraph("3. Spatial Context (nearest infrastructure)", h2))
    if ftr:
        rows = [
            ("Nearest refinery", f"{ftr.nearest_refinery_distance:.2f} km"),
            ("Nearest factory", f"{ftr.nearest_factory_distance:.2f} km"),
            ("Nearest power plant", f"{ftr.nearest_powerplant_distance:.2f} km"),
            ("Nearest mine", f"{ftr.nearest_mine_distance:.2f} km"),
            ("Nearest forest", f"{ftr.nearest_forest_distance:.2f} km"),
            ("Nearest agricultural area", f"{ftr.nearest_agriculture_distance:.2f} km"),
            ("Nearest settlement", f"{ftr.nearest_settlement_distance:.2f} km"),
            ("Nearest road", f"{ftr.nearest_road_distance:.2f} km"),
            ("Nearest railway", f"{ftr.nearest_railway_distance:.2f} km"),
            ("Nearest pipeline", f"{ftr.nearest_pipeline_distance:.2f} km"),
        ]
        story.append(_kv_table(rows))

    story.append(Paragraph("4. AI Explanation", h2))
    exp = hotspot.explanation or {}
    factors = exp.get("model_derived_factors", {})
    if factors:
        story.append(_kv_table([(k, str(v)) for k, v in factors.items()]))
    reasoning = exp.get("reasoning", "")
    story.append(Paragraph(f"Contextual reasoning: {reasoning}", body))
    story.append(Paragraph("Note: model-derived factors come from the trained classifier; contextual factors are rule-based.", small))

    story.append(Paragraph("5. Temporal History", h2))
    hist = sorted(hotspot.history, key=lambda h: h.detection_time)
    if hist:
        rows = [("Detection time", "Brightness (K)", "FRP (MW)")] + [
            (h.detection_time.strftime("%Y-%m-%d %H:%M"), f"{h.brightness:.1f}", f"{h.frp:.1f}") for h in hist
        ]
        t = Table(rows, colWidths=[60 * mm, 55 * mm, 55 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t)
    else:
        story.append(Paragraph("No prior detections - first detection at this location.", body))

    story.append(Paragraph("6. Classification History", h2))
    story.append(
        Paragraph(
            f"Current: <font color='{_classification_color(hotspot.classification)}'><b>{hotspot.classification}</b></font> "
            f"(confidence {hotspot.classification_confidence * 100:.0f}%)",
            body,
        )
    )

    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Generated by FIRE-X v1.0 - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", small))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def build_daily_report(db: Session, days: int = 1) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=22 * mm, bottomMargin=16 * mm)
    title, subtitle, h2, body, small = _styles()
    since = datetime.now(timezone.utc) - __import__("datetime", fromlist=["timedelta"]).timedelta(days=days)
    hotspots = db.query(Hotspot).filter(Hotspot.acquisition_time >= since).order_by(Hotspot.risk_score.desc()).all()
    alerts = db.query(Alert).filter(Alert.created_at >= since).all()

    story = [
        Paragraph("FIRE-X", title),
        Paragraph(f"Daily Intelligence Report - last {days} day(s)", subtitle),
        Spacer(1, 8),
        Paragraph(f"Hotspots detected: {len(hotspots)} | Alerts generated: {len(alerts)}", body),
        Spacer(1, 6),
    ]
    if hotspots:
        rows = [("ID", "Classification", "Risk", "State", "Detected")] + [
            (
                h.code,
                h.classification,
                f"{h.risk_score:.0f} {h.risk_level}",
                h.state,
                h.acquisition_time.strftime("%m-%d %H:%M") if h.acquisition_time else "-",
            )
            for h in hotspots[:60]
        ]
        t = Table(rows, colWidths=[22 * mm, 52 * mm, 30 * mm, 40 * mm, 36 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t)
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def build_zone_report(db: Session, zone: IndustrialZone) -> bytes:
    from app.gis.engine import haversine_km

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=22 * mm, bottomMargin=16 * mm)
    title, subtitle, h2, body, small = _styles()
    near = [h for h in db.query(Hotspot).all() if haversine_km(zone.latitude, zone.longitude, h.latitude, h.longitude) <= zone.radius_km]
    story = [
        Paragraph("FIRE-X", title),
        Paragraph("Industrial Zone Report", subtitle),
        Spacer(1, 8),
        _kv_table(
            [
                ("Zone", zone.name),
                ("Type", zone.zone_type),
                ("Location", f"{zone.latitude:.4f}, {zone.longitude:.4f} ({zone.district}, {zone.state})"),
                ("Current risk", f"{zone.risk_level}"),
                ("Monitoring level", zone.monitoring_level),
                ("Population exposure", str(zone.population_exposure)),
                ("Hotspots within radius", str(len(near))),
            ]
        ),
    ]
    if near:
        rows = [("ID", "Classification", "Risk", "Distance (km)")] + [
            (
                h.code,
                h.classification,
                f"{h.risk_score:.0f} {h.risk_level}",
                f"{haversine_km(zone.latitude, zone.longitude, h.latitude, h.longitude):.2f}",
            )
            for h in sorted(near, key=lambda h: h.risk_score, reverse=True)[:25]
        ]
        t = Table(rows, colWidths=[22 * mm, 52 * mm, 30 * mm, 36 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(Paragraph("Nearby hotspots", h2))
        story.append(t)
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def _action_for(level: str) -> str:
    return {
        "CRITICAL": "Immediate field verification recommended.",
        "HIGH": "Priority inspection recommended.",
        "ELEVATED": "Enhanced monitoring recommended.",
        "MODERATE": "Continue monitoring.",
        "LOW": "No immediate action required.",
    }.get(level, "Continue monitoring.")