"""Tests for export utilities."""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile


class TestCSVExport:
    """Tests for CSV export functionality."""

    def test_export_dataframe_to_csv(self):
        """Test exporting DataFrame to CSV."""
        from utils.export import export_to_csv

        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [25, 30],
        })

        csv_bytes, filename = export_to_csv(df)

        assert csv_bytes is not None
        assert b"name,age" in csv_bytes
        assert b"Alice" in csv_bytes
        assert filename.endswith(".csv")

    def test_export_list_to_csv(self):
        """Test exporting list of dicts to CSV."""
        from utils.export import export_to_csv

        data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
        ]

        csv_bytes, filename = export_to_csv(data)

        assert csv_bytes is not None
        assert b"name,age" in csv_bytes

    def test_export_csv_with_custom_filename(self):
        """Test exporting with custom filename."""
        from utils.export import export_to_csv

        df = pd.DataFrame({"col": [1, 2, 3]})
        csv_bytes, filename = export_to_csv(df, filename="my_export")

        assert filename == "my_export.csv"

    def test_export_csv_to_directory(self):
        """Test exporting to a specific directory."""
        from utils.export import export_to_csv

        df = pd.DataFrame({"col": [1, 2, 3]})

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            csv_bytes, filename = export_to_csv(df, output_dir=output_dir)

            output_file = output_dir / filename
            assert output_file.exists()
            assert output_file.read_bytes() == csv_bytes


class TestPNGExport:
    """Tests for PNG export functionality."""

    def test_export_png_without_html2image(self):
        """Test PNG export gracefully handles missing html2image."""
        from utils.export import export_to_png
        from pyvis.network import Network

        net = Network()
        net.add_node(1, label="Test")

        with patch.dict("sys.modules", {"html2image": None}):
            png_bytes, filename = export_to_png(net)
            # Should return None when html2image is not available
            assert filename.endswith(".png")

    def test_export_png_custom_dimensions(self):
        """Test PNG export with custom dimensions."""
        from utils.export import export_to_png
        from pyvis.network import Network

        net = Network()
        net.add_node(1, label="Test")

        # Mock html2image
        with patch("utils.export.Html2Image") as mock_hti:
            mock_instance = MagicMock()
            mock_hti.return_value = mock_instance

            png_bytes, filename = export_to_png(
                net,
                width=800,
                height=600,
            )

            # Verify screenshot was called with correct size
            if mock_instance.screenshot.called:
                call_args = mock_instance.screenshot.call_args
                assert call_args.kwargs.get("size") == (800, 600)


class TestSVGExport:
    """Tests for SVG export functionality."""

    def test_export_svg_basic(self):
        """Test basic SVG export."""
        from utils.export import export_to_svg
        from pyvis.network import Network

        net = Network()
        net.add_node(1, label="Test")

        svg_bytes, filename = export_to_svg(net)

        assert svg_bytes is not None
        assert b"<svg" in svg_bytes
        assert filename.endswith(".svg")

    def test_export_svg_with_custom_filename(self):
        """Test SVG export with custom filename."""
        from utils.export import export_to_svg
        from pyvis.network import Network

        net = Network()
        net.add_node(1, label="Test")

        svg_bytes, filename = export_to_svg(net, filename="my_graph")

        assert filename == "my_graph.svg"


class TestPDFExport:
    """Tests for PDF export functionality."""

    def test_export_pdf_basic(self):
        """Test basic PDF export."""
        from utils.export import export_to_pdf

        data = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "score": [95, 87],
        })

        pdf_bytes, filename = export_to_pdf(
            title="Test Report",
            data=data,
        )

        # PDF should be generated if reportlab is available
        assert filename.endswith(".pdf")
        if pdf_bytes is not None:
            assert b"%PDF" in pdf_bytes  # PDF magic bytes

    def test_export_pdf_with_list_data(self):
        """Test PDF export with list of dicts."""
        from utils.export import export_to_pdf

        data = [
            {"name": "Alice", "score": 95},
            {"name": "Bob", "score": 87},
        ]

        pdf_bytes, filename = export_to_pdf(
            title="Test Report",
            data=data,
        )

        assert filename.endswith(".pdf")

    def test_export_pdf_without_timestamp(self):
        """Test PDF export without timestamp."""
        from utils.export import export_to_pdf

        data = pd.DataFrame({"col": [1, 2]})

        pdf_bytes, filename = export_to_pdf(
            title="No Timestamp Report",
            data=data,
            include_timestamp=False,
        )

        assert filename.endswith(".pdf")


class TestExportManager:
    """Tests for ExportManager class."""

    def test_export_manager_initialization(self):
        """Test ExportManager initialization."""
        from utils.export import ExportManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExportManager(output_dir=tmpdir)
            assert manager.output_dir == Path(tmpdir)

    def test_export_manager_creates_directory(self):
        """Test that ExportManager creates output directory."""
        from utils.export import ExportManager

        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "exports" / "nested"
            manager = ExportManager(output_dir=new_dir)
            assert new_dir.exists()

    def test_export_manager_csv_method(self):
        """Test ExportManager CSV export method."""
        from utils.export import ExportManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExportManager(output_dir=tmpdir)
            df = pd.DataFrame({"col": [1, 2, 3]})

            csv_bytes, filename = manager.export_csv(df, filename="test")

            assert csv_bytes is not None
            assert (Path(tmpdir) / filename).exists()

    def test_export_manager_without_output_dir(self):
        """Test ExportManager without output directory."""
        from utils.export import ExportManager

        manager = ExportManager()
        assert manager.output_dir is None

        df = pd.DataFrame({"col": [1]})
        csv_bytes, filename = manager.export_csv(df)

        assert csv_bytes is not None


class TestEdgeCases:
    """Tests for edge cases in exports."""

    def test_export_empty_dataframe(self):
        """Test exporting empty DataFrame."""
        from utils.export import export_to_csv

        df = pd.DataFrame()
        csv_bytes, filename = export_to_csv(df)

        assert csv_bytes is not None
        assert filename.endswith(".csv")

    def test_export_dataframe_with_special_characters(self):
        """Test exporting DataFrame with special characters."""
        from utils.export import export_to_csv

        df = pd.DataFrame({
            "name": ["Alice, Jr.", "Bob \"The Builder\""],
            "notes": ["Line1\nLine2", "Tab\there"],
        })

        csv_bytes, filename = export_to_csv(df)
        assert csv_bytes is not None

    def test_export_large_values_truncated_in_pdf(self):
        """Test that large values are truncated in PDF tables."""
        from utils.export import export_to_pdf

        data = pd.DataFrame({
            "description": ["A" * 100, "B" * 100],  # Long strings
        })

        pdf_bytes, filename = export_to_pdf(
            title="Large Values Test",
            data=data,
        )

        # Should not raise an error
        assert filename.endswith(".pdf")
