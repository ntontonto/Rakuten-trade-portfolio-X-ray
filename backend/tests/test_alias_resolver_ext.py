from app.services.alias_resolver import resolve_alias


def test_resolve_numeric_t_suffix_variants():
    fetch_symbol, _ = resolve_alias("1693.T", "ＷＴ銅上場投信")
    assert fetch_symbol == "1693"

    fetch_symbol2, _ = resolve_alias("4755.T", "楽天グループ")
    assert fetch_symbol2 == "4755"


def test_resolve_name_variants_with_spaces():
    fetch_symbol, _ = resolve_alias("", "ＷＴ 銅 上場投信")
    assert fetch_symbol == "1693"

    fetch_symbol2, _ = resolve_alias("", "楽天 グループ")
    assert fetch_symbol2 == "4755"
