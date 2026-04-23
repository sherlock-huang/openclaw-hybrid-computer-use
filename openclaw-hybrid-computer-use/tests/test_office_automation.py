"""Office 自动化测试"""

import os
import pytest
from pathlib import Path

from claw_desktop.action.office_automation import ExcelController, WordController


class TestExcelController:
    def test_create_and_write_cell(self, tmp_path):
        filepath = tmp_path / "test.xlsx"
        excel = ExcelController().create(str(filepath))
        excel.write_cell("A1", "Hello")
        excel.write_cell("B1", 42)
        excel.save()
        assert filepath.exists()
        assert filepath.stat().st_size > 0

    def test_write_range_and_chart(self, tmp_path):
        filepath = tmp_path / "chart.xlsx"
        excel = ExcelController().create(str(filepath))
        excel.write_range("A1", [["Name", "Score"], ["A", 80], ["B", 90]])
        excel.create_chart("bar", "A1:B3", "Scores", position="D2")
        excel.save()
        assert filepath.exists()

    def test_read_cell(self, tmp_path):
        filepath = tmp_path / "read.xlsx"
        excel = ExcelController().create(str(filepath))
        excel.write_cell("C3", "test_value")
        excel.save()
        excel2 = ExcelController().open(str(filepath))
        val = excel2.read_cell("C3")
        assert val == "test_value"


class TestWordController:
    def test_create_and_save(self, tmp_path):
        filepath = tmp_path / "test.docx"
        word = WordController().create(str(filepath))
        word.add_heading("Title", level=1)
        word.add_paragraph("Hello World")
        word.save()
        assert filepath.exists()
        assert filepath.stat().st_size > 0

    def test_fill_template(self, tmp_path):
        filepath = tmp_path / "template.docx"
        word = WordController().create(str(filepath))
        word.add_paragraph("Dear {{NAME}}, welcome to {{COMPANY}}.")
        word.save()

        word2 = WordController().open(str(filepath))
        count = word2.fill_template({"{{NAME}}": "Alice", "{{COMPANY}}": "OpenClaw"})
        assert count == 2
        word2.save(str(tmp_path / "filled.docx"))