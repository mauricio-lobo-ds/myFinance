from tests.conftest import mock_sheet
import db.sheets as sheets


SAMPLE_ROWS = [
    {"timestamp": "2026-05-01T10:00:00", "user_id": 123, "username": "mauricio",
     "mensagem_original": "Almoço 35", "valor": 35.0, "categoria": "Alimentação",
     "descricao": "Almoço", "data_gasto": "2026-05-01", "telegram_file_id": ""},
    {"timestamp": "2026-05-10T12:00:00", "user_id": 123, "username": "mauricio",
     "mensagem_original": "Condomínio 850", "valor": 850.0, "categoria": "Moradia",
     "descricao": "Condomínio", "data_gasto": "2026-05-10", "telegram_file_id": "abc123"},
    {"timestamp": "2026-04-15T09:00:00", "user_id": 123, "username": "mauricio",
     "mensagem_original": "Netflix 45", "valor": 45.9, "categoria": "Streaming",
     "descricao": "Netflix", "data_gasto": "2026-04-15", "telegram_file_id": ""},
    {"timestamp": "2026-05-05T08:00:00", "user_id": 999, "username": "outro",
     "mensagem_original": "Gasolina 100", "valor": 100.0, "categoria": "Transporte",
     "descricao": "Gasolina", "data_gasto": "2026-05-05", "telegram_file_id": ""},
]


def setup_function():
    mock_sheet.get_all_records.return_value = SAMPLE_ROWS


# --- get_gastos ---

def test_get_gastos_by_month_returns_only_that_month():
    result = sheets.get_gastos(123, "2026-05")
    assert len(result) == 2
    assert all(r["data_gasto"].startswith("2026-05") for r in result)


def test_get_gastos_by_year_returns_all_months():
    result = sheets.get_gastos(123, "2026")
    assert len(result) == 3


def test_get_gastos_no_period_returns_all_user_rows():
    result = sheets.get_gastos(123)
    assert len(result) == 3


def test_get_gastos_isolates_by_user():
    result = sheets.get_gastos(999, "2026-05")
    assert len(result) == 1
    assert result[0]["username"] == "outro"


def test_get_gastos_unknown_user_returns_empty():
    result = sheets.get_gastos(777, "2026-05")
    assert result == []


# --- get_comprovantes ---

def test_get_comprovantes_returns_only_rows_with_file_id():
    result = sheets.get_comprovantes(123)
    assert len(result) == 1
    assert result[0]["telegram_file_id"] == "abc123"


def test_get_comprovantes_filters_by_month():
    result = sheets.get_comprovantes(123, "2026-04")
    assert result == []


def test_get_comprovantes_correct_month():
    result = sheets.get_comprovantes(123, "2026-05")
    assert len(result) == 1


# --- save_to_db ---

def test_save_to_db_calls_append_row_with_all_columns():
    data = {
        "timestamp": "2026-05-11T20:00:00",
        "user_id": 123,
        "username": "mauricio",
        "mensagem_original": "Taxi 30",
        "valor": 30.0,
        "categoria": "Transporte",
        "descricao": "Taxi",
        "data_gasto": "2026-05-11",
        "telegram_file_id": "xyz",
    }
    sheets.save_to_db(data)
    mock_sheet.append_row.assert_called_once_with([
        "2026-05-11T20:00:00", 123, "mauricio", "Taxi 30",
        30.0, "Transporte", "Taxi", "2026-05-11", "xyz",
    ])
    mock_sheet.append_row.reset_mock()


def test_save_to_db_missing_file_id_saves_empty_string():
    data = {
        "timestamp": "t", "user_id": 1, "username": "u",
        "mensagem_original": "m", "valor": 10.0,
        "categoria": "Outros", "descricao": "d", "data_gasto": "2026-05-11",
    }
    sheets.save_to_db(data)
    args = mock_sheet.append_row.call_args[0][0]
    assert args[8] == ""
    mock_sheet.append_row.reset_mock()
