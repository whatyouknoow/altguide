#!/usr/bin/env python3
"""
Тесты для проверки BOM файлов.
Запуск: pytest test_bom.py -v
"""

import sys
import os
import shutil
import tempfile
import pytest
from io import StringIO

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bom import bom_check


# Определяем тестовые данные
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture
def temp_bom_dir():
    """Фикстура для создания временной директории"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def run_bom_check(test_file_path, temp_dir):
    """
    Запускает проверку BOM и возвращает вывод
    
    Args:
        test_file_path: Путь к тестовому BOM файлу
        temp_dir: Временная директория
        
    Returns:
        tuple: (success: bool, output: str)
    """
    # Копируем тестовый файл как "Bill of Materials.csv"
    temp_file = os.path.join(temp_dir, "Bill of Materials.csv")
    shutil.copy2(test_file_path, temp_file)
    
    # Перехватываем stdout для анализа вывода
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        bom_check(temp_dir + "/")
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return True, output
    except SystemExit:
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return False, output
    except Exception as e:
        sys.stdout = old_stdout
        return False, str(e)


# Тесты на успешное прохождение
def test_valid_bom(temp_bom_dir):
    """Тест валидного BOM файла"""
    test_file = os.path.join(TEST_DATA_DIR, "Bill of Materials-valid.csv")
    success, output = run_bom_check(test_file, temp_bom_dir)
    assert success, f"Ожидалось успешное выполнение, но получена ошибка: {output}"


# Тесты на обнаружение ошибок
@pytest.mark.parametrize("test_file,expected_error", [
    ("Bill of Materials-empty_part.csv", "поля Part в элементе"),
    ("Bill of Materials-empty_description.csv", "поля Description в элементе"),
    ("Bill of Materials-empty_designator.csv", "поля Designator в строке"),
    ("Bill of Materials-empty_footprint.csv", "поля Footprint в элементе"),
    ("Bill of Materials-m3_component.csv", "компоненты"),
    ("Bill of Materials-wrong_headers.csv", "заголовков"),
    ("Bill of Materials-extra_empty_line.csv", "пустая строка"),
])
def test_bom_errors(temp_bom_dir, test_file, expected_error):
    """Параметризованный тест для различных ошибок в BOM"""
    test_file_path = os.path.join(TEST_DATA_DIR, test_file)
    success, output = run_bom_check(test_file_path, temp_bom_dir)

    assert not success, f"Ожидалась ошибка, но проверка прошла успешно"
    assert expected_error in output, f"Ожидаемая ошибка '{expected_error}' не найдена в выводе: {output}"


# Тесты на дублирование значений
@pytest.mark.parametrize("test_file,col_name,expected_error", [
    ("Bill of Materials-duplicate_part.csv", "Part", "дублирующееся значение 'CC0603JPX7R9BB104' в столбце 'Part'"),
    ("Bill of Materials-duplicate_alt_part.csv", "Alternative Part", "дублирующееся значение 'C100nF' в столбце 'Alternative Part'"),
    ("Bill of Materials-duplicate_jlcpcb_part.csv", "JLCPCB Part", "дублирующееся значение 'C100nF' в столбце 'JLCPCB Part'"),
    ("Bill of Materials-duplicate_multiple.csv", "Part", "дублирующееся значение 'CC0603JPX7R9BB104' в столбце 'Part'"),
])
def test_bom_duplicate_values(temp_bom_dir, test_file, col_name, expected_error):
    """Тест на дублирование значений в столбцах Part, Alternative Part, JLCPCB Part"""
    test_file_path = os.path.join(TEST_DATA_DIR, test_file)
    success, output = run_bom_check(test_file_path, temp_bom_dir)

    assert not success, f"Ожидалась ошибка дублирования, но проверка прошла успешно"
    assert expected_error in output, f"Ожидаемая ошибка '{expected_error}' не найдена в выводе: {output}"


# Тесты для специфичных проверок
def test_altium_empty_line_ignored(temp_bom_dir):
    """Тест что первая пустая строка Altium игнорируется"""
    test_file = os.path.join(TEST_DATA_DIR, "Bill of Materials-valid.csv")
    success, output = run_bom_check(test_file, temp_bom_dir)
    assert "стандартная строка Altium" in output or "проигнорирована" in output


def test_multiple_part_errors(temp_bom_dir):
    """Тест что все ошибки Part собираются"""
    test_file = os.path.join(TEST_DATA_DIR, "Bill of Materials-empty_part.csv")
    success, output = run_bom_check(test_file, temp_bom_dir)
    
    # Проверяем что есть несколько строк с ошибками Part (если в файле их несколько)
    error_lines = [line for line in output.split('\n') if 'поля Part' in line]
    assert len(error_lines) >= 1, "Должна быть хотя бы одна ошибка Part"


if __name__ == "__main__":
    # Запуск pytest программно
    pytest.main([__file__, "-v"])
