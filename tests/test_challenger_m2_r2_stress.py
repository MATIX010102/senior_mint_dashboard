"""
Adversarial Stress Test Suite for Milestone M2 Iteration 2 (Challenger M2 R2 2).
Empirically tests:
1. WeatherWidget with null JSON cache values and missing fields.
2. WeatherWidget constructor signature variations (parent, cache_file, str paths).
3. PrinterWidget constructor signature variations (parent, default_printer string).
4. SeniorDashboardWindow instantiation without attribute/type misalignment errors.
5. PrinterWidget CUPS error status and print_test_page error handling.
"""

import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure offscreen Qt platform for headless test execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtWidgets import QApplication, QWidget, QFrame
from PyQt6.QtCore import Qt

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# ============================================================================
# 1. WEATHER WIDGET NULL CACHE & CORRUPTION STRESS TESTS
# ============================================================================

def test_weather_widget_null_json_values(qapp, tmp_path):
    """Stress test WeatherWidget with JSON cache containing explicit null values."""
    from senior_mint_dashboard.launcher.widgets.weather_widget import WeatherWidget

    cache_file = tmp_path / "null_cache.json"
    cache_file.write_text(json.dumps({
        "city": None,
        "temp": None,
        "condition": None,
        "icon": None
    }), encoding="utf-8")

    widget = WeatherWidget(cache_file=cache_file)
    
    # load_cache must fallback or return default because temp & condition are None
    data = widget.load_cache()
    assert data["temp"] == "--°C", f"Expected '--°C', got {data.get('temp')}"
    assert data["condition"] == "Brak danych o pogodzie"

    # Direct update_display call with null values
    widget.update_display({"city": None, "temp": None, "condition": None})
    assert widget.temp_label.text() == "--°C"
    assert widget.condition_label.text() == "Brak danych o pogodzie"


def test_weather_widget_partial_null_values(qapp, tmp_path):
    """Stress test WeatherWidget with partial null values in cache."""
    from senior_mint_dashboard.launcher.widgets.weather_widget import WeatherWidget

    # Case A: temp is null, condition is valid string
    cache_file_a = tmp_path / "cache_a.json"
    cache_file_a.write_text(json.dumps({"temp": None, "condition": "Słonecznie"}), encoding="utf-8")
    widget_a = WeatherWidget(cache_file=cache_file_a)
    data_a = widget_a.load_cache()
    assert data_a["temp"] == "--°C"

    # Case B: temp is valid string, condition is null
    cache_file_b = tmp_path / "cache_b.json"
    cache_file_b.write_text(json.dumps({"temp": "+18°C", "condition": None}), encoding="utf-8")
    widget_b = WeatherWidget(cache_file=cache_file_b)
    data_b = widget_b.load_cache()
    assert data_b["condition"] == "Brak danych o pogodzie"

    # Case C: update_display with partial nulls
    widget_a.update_display({"city": "Kraków", "temp": None, "condition": "Deszczowo"})
    assert widget_a.temp_label.text() == "--°C"
    assert widget_a.condition_label.text() == "Deszczowo"


def test_weather_widget_non_dict_json(qapp, tmp_path):
    """Stress test WeatherWidget with non-dict JSON values (lists, ints, strings)."""
    from senior_mint_dashboard.launcher.widgets.weather_widget import WeatherWidget

    cache_file = tmp_path / "list_cache.json"
    cache_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    widget = WeatherWidget(cache_file=cache_file)
    data = widget.load_cache()
    assert data == WeatherWidget.DEFAULT_FALLBACK_DATA


# ============================================================================
# 2. WEATHER WIDGET CONSTRUCTOR VARIATIONS STRESS TESTS
# ============================================================================

def test_weather_widget_constructor_variations(qapp, tmp_path):
    """Stress test all constructor calling conventions for WeatherWidget."""
    from senior_mint_dashboard.launcher.widgets.weather_widget import WeatherWidget

    parent_w = QWidget()
    c_path = tmp_path / "custom_weather.json"

    # Convention 1: WeatherWidget()
    w1 = WeatherWidget()
    assert w1.parent() is None
    assert isinstance(w1.cache_file, Path)

    # Convention 2: WeatherWidget(parent_widget)
    w2 = WeatherWidget(parent_w)
    assert w2.parent() == parent_w
    assert isinstance(w2.cache_file, Path)
    assert not isinstance(w2.cache_file, QWidget)

    # Convention 3: WeatherWidget(cache_file_path) as positional Path
    w3 = WeatherWidget(c_path)
    assert w3.parent() is None
    assert w3.cache_file == c_path

    # Convention 4: WeatherWidget(str_path) as positional str
    w4 = WeatherWidget(str(c_path))
    assert w4.parent() is None
    assert w4.cache_file == c_path

    # Convention 5: WeatherWidget(parent=parent_w, cache_file=c_path)
    w5 = WeatherWidget(parent=parent_w, cache_file=c_path)
    assert w5.parent() == parent_w
    assert w5.cache_file == c_path

    # Convention 6: WeatherWidget(parent=parent_w)
    w6 = WeatherWidget(parent=parent_w)
    assert w6.parent() == parent_w
    assert isinstance(w6.cache_file, Path)


# ============================================================================
# 3. PRINTER WIDGET CONSTRUCTOR VARIATIONS STRESS TESTS
# ============================================================================

def test_printer_widget_constructor_variations(qapp):
    """Stress test all constructor calling conventions for PrinterWidget."""
    from senior_mint_dashboard.launcher.widgets.printer_widget import PrinterWidget

    parent_w = QWidget()
    custom_printer = "HP_LaserJet_P1102"

    # Convention 1: PrinterWidget()
    p1 = PrinterWidget()
    assert p1.parent() is None
    assert p1.default_printer == PrinterWidget.DEFAULT_PRINTER

    # Convention 2: PrinterWidget(parent_widget)
    p2 = PrinterWidget(parent_w)
    assert p2.parent() == parent_w
    assert p2.default_printer == PrinterWidget.DEFAULT_PRINTER

    # Convention 3: PrinterWidget(custom_printer_name) as positional str
    p3 = PrinterWidget(custom_printer)
    assert p3.parent() is None
    assert p3.default_printer == custom_printer

    # Convention 4: PrinterWidget(parent=parent_w, default_printer=custom_printer)
    p4 = PrinterWidget(parent=parent_w, default_printer=custom_printer)
    assert p4.parent() == parent_w
    assert p4.default_printer == custom_printer

    # Convention 5: PrinterWidget(parent=parent_w)
    p5 = PrinterWidget(parent=parent_w)
    assert p5.parent() == parent_w
    assert p5.default_printer == PrinterWidget.DEFAULT_PRINTER


# ============================================================================
# 4. SENIOR DASHBOARD WINDOW INSTANTIATION STRESS TEST
# ============================================================================

def test_senior_dashboard_window_instantiation_integrity(qapp):
    """Verify SeniorDashboardWindow initializes cleanly and sub-widgets have correct parents/attributes."""
    from senior_mint_dashboard.launcher.main_window import SeniorDashboardWindow

    win = SeniorDashboardWindow()
    assert win is not None
    assert win.windowTitle() == "Senior Mint Dashboard"

    # Check WeatherWidget integration
    assert win.weather_widget is not None
    assert win.weather_widget.window() == win
    assert win.weather_widget.parent() == win.ui_overlay
    assert isinstance(win.weather_widget.cache_file, Path)
    assert win.weather_widget.cache_file != win  # Ensures parent wasn't passed as cache_file!

    # Check PrinterWidget integration
    assert win.printer_widget is not None
    assert win.printer_widget.window() == win
    assert win.printer_widget.parent() == win.ui_overlay
    assert isinstance(win.printer_widget.default_printer, str)
    assert win.printer_widget.default_printer == "HP_DeskJet_2130"
    assert win.printer_widget.default_printer != win  # Ensures parent wasn't passed as printer name!

    win.close()


# ============================================================================
# 5. PRINTER WIDGET CUPS ERROR HANDLING STRESS TEST
# ============================================================================

def test_printer_widget_cups_error_handling(qapp):
    """Stress test PrinterWidget when CUPS or lpstat is unavailable or errors out."""
    from senior_mint_dashboard.launcher.widgets.printer_widget import PrinterWidget

    p = PrinterWidget()

    # Scenario A: lpstat missing
    with patch("shutil.which", return_value=None):
        online, msg = p.check_printer_status()
        assert online is False
        assert "Brak usługi druku" in msg

    # Scenario B: lpstat subprocess error
    with patch("shutil.which", return_value="/usr/bin/lpstat"):
        with patch("subprocess.run", side_effect=FileNotFoundError("lpstat not found")):
            online, msg = p.check_printer_status()
            assert online is False
            assert "Błąd połączenia" in msg

    # Scenario C: print_test_page when offline triggers warning dialog
    with patch("shutil.which", return_value=None):
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warn:
            success = p.print_test_page()
            assert success is False
            mock_warn.assert_called_once()
