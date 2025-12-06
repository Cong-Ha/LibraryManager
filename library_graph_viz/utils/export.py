"""Export utilities for graphs and data."""

import io
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
from pyvis.network import Network

logger = logging.getLogger(__name__)


def export_to_csv(
    data: Union[pd.DataFrame, list[dict]],
    filename: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> tuple[bytes, str]:
    """
    Export data to CSV format.

    Args:
        data: DataFrame or list of dictionaries to export.
        filename: Optional filename (without extension).
        output_dir: Optional output directory path.

    Returns:
        Tuple of (CSV bytes, filename).
    """
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data

    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    csv_bytes = df.to_csv(index=False).encode("utf-8")

    if output_dir:
        output_path = output_dir / f"{filename}.csv"
        output_path.write_bytes(csv_bytes)
        logger.info(f"Exported CSV to {output_path}")

    return csv_bytes, f"{filename}.csv"


def export_to_png(
    network: Network,
    filename: Optional[str] = None,
    output_dir: Optional[Path] = None,
    width: int = 1200,
    height: int = 800,
) -> tuple[Optional[bytes], str]:
    """
    Export PyVis network to PNG image.

    Requires html2image package to be installed.

    Args:
        network: PyVis Network instance.
        filename: Optional filename (without extension).
        output_dir: Optional output directory path.
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        Tuple of (PNG bytes or None if failed, filename).
    """
    try:
        from html2image import Html2Image

        if filename is None:
            filename = f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Generate HTML
        html_content = network.generate_html()

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            hti = Html2Image(output_path=tmpdir)
            hti.screenshot(
                html_str=html_content,
                save_as=f"{filename}.png",
                size=(width, height),
            )

            # Read the generated PNG
            png_path = Path(tmpdir) / f"{filename}.png"
            if png_path.exists():
                png_bytes = png_path.read_bytes()

                if output_dir:
                    output_path = output_dir / f"{filename}.png"
                    output_path.write_bytes(png_bytes)
                    logger.info(f"Exported PNG to {output_path}")

                return png_bytes, f"{filename}.png"

        logger.warning("PNG export failed: file not generated")
        return None, f"{filename}.png"

    except ImportError:
        logger.error("html2image package not installed. Run: pip install html2image")
        return None, f"{filename}.png"
    except Exception as e:
        logger.error(f"PNG export failed: {e}")
        return None, f"{filename}.png"


def export_to_svg(
    network: Network,
    filename: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> tuple[bytes, str]:
    """
    Export PyVis network to SVG format.

    Note: This exports the HTML representation as an embedded SVG is not
    directly supported by PyVis. For full SVG support, consider using
    a different visualization library.

    Args:
        network: PyVis Network instance.
        filename: Optional filename (without extension).
        output_dir: Optional output directory path.

    Returns:
        Tuple of (SVG-like HTML bytes, filename).
    """
    if filename is None:
        filename = f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # PyVis doesn't natively support SVG, so we export the HTML
    html_content = network.generate_html()

    # Create a simple SVG wrapper with embedded HTML
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <foreignObject width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml">
            {html_content}
        </div>
    </foreignObject>
</svg>"""

    svg_bytes = svg_content.encode("utf-8")

    if output_dir:
        output_path = output_dir / f"{filename}.svg"
        output_path.write_bytes(svg_bytes)
        logger.info(f"Exported SVG to {output_path}")

    return svg_bytes, f"{filename}.svg"


def export_to_pdf(
    title: str,
    data: Union[pd.DataFrame, list[dict]],
    network_html: Optional[str] = None,
    filename: Optional[str] = None,
    output_dir: Optional[Path] = None,
    include_timestamp: bool = True,
) -> tuple[Optional[bytes], str]:
    """
    Export data and optionally graph to PDF report.

    Requires reportlab package to be installed.

    Args:
        title: Report title.
        data: DataFrame or list of dictionaries for the data table.
        network_html: Optional HTML string of the network graph.
        filename: Optional filename (without extension).
        output_dir: Optional output directory path.
        include_timestamp: Whether to include timestamp in the report.

    Returns:
        Tuple of (PDF bytes or None if failed, filename).
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
        )

        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
        )
        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.gray,
            alignment=1,
        )

        # Build content
        story = []

        # Title
        story.append(Paragraph(title, title_style))

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            story.append(Paragraph(f"Generated: {timestamp}", subtitle_style))

        story.append(Spacer(1, 30))

        # Data table
        if not df.empty:
            story.append(Paragraph("Data Summary", styles["Heading2"]))
            story.append(Spacer(1, 10))

            # Convert DataFrame to table data
            table_data = [df.columns.tolist()] + df.values.tolist()

            # Truncate long values
            table_data = [
                [str(cell)[:50] + "..." if len(str(cell)) > 50 else str(cell) for cell in row]
                for row in table_data
            ]

            # Create table
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ]))

            story.append(table)

        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "Library Graph Visualization - Generated with Neo4j + PyVis + Streamlit",
            subtitle_style,
        ))

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        if output_dir:
            output_path = output_dir / f"{filename}.pdf"
            output_path.write_bytes(pdf_bytes)
            logger.info(f"Exported PDF to {output_path}")

        return pdf_bytes, f"{filename}.pdf"

    except ImportError:
        logger.error("reportlab package not installed. Run: pip install reportlab")
        return None, f"{filename}.pdf"
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        return None, f"{filename}.pdf"


class ExportManager:
    """
    Manager class for handling exports with consistent settings.
    """

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """
        Initialize export manager.

        Args:
            output_dir: Default output directory for exports.
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.output_dir = None

    def export_csv(
        self,
        data: Union[pd.DataFrame, list[dict]],
        filename: Optional[str] = None,
    ) -> tuple[bytes, str]:
        """Export data to CSV."""
        return export_to_csv(data, filename, self.output_dir)

    def export_png(
        self,
        network: Network,
        filename: Optional[str] = None,
        width: int = 1200,
        height: int = 800,
    ) -> tuple[Optional[bytes], str]:
        """Export network to PNG."""
        return export_to_png(network, filename, self.output_dir, width, height)

    def export_svg(
        self,
        network: Network,
        filename: Optional[str] = None,
    ) -> tuple[bytes, str]:
        """Export network to SVG."""
        return export_to_svg(network, filename, self.output_dir)

    def export_pdf(
        self,
        title: str,
        data: Union[pd.DataFrame, list[dict]],
        network_html: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> tuple[Optional[bytes], str]:
        """Export report to PDF."""
        return export_to_pdf(title, data, network_html, filename, self.output_dir)
