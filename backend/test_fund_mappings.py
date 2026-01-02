"""
Test all new fund mappings
"""
from app.services.alias_resolver import resolve_alias

def test_all_mappings():
    """Test that all fund mappings resolve correctly"""

    test_cases = [
        # eMAXIS Slim funds
        ("eMAXIS Slim 全世界株式(オール・カントリー)(オルカン)", "0331418A"),
        ("オルカン", "0331418A"),
        ("eMAXIS Slim 米国株式(S&P500)", "03311187"),
        ("eMAXIS Slim 先進国債券インデックス(除く日本)", "0331A172"),
        ("eMAXIS Slim 先進国リートインデックス(除く日本)", "0331219A"),

        # Other mutual funds
        ("NZAM・ベータ 米国REIT", "25314203"),
        ("たわらノーロード インド株式Nifty50", "4731624C"),
        ("ニッセイSOX指数インデックスファンド", "29314233"),
        ("三菱UFJ 純金ファンド(ファインゴールド)", "03311112"),
        ("iFreeNEXT FANG+インデックス", "04311181"),
        ("野村Jリートファンド", "01314133"),

        # Short name aliases
        ("先進国債券インデックス(除く日本)", "0331A172"),
        ("インド株式Nifty50", "4731624C"),
        ("SOX指数インデックスファンド", "29314233"),
        ("FANG+インデックス", "04311181"),

        # Japanese ETFs
        ("ＳＰＤＲゴールド・シェア（東証上場）", "1326"),
        ("ＳＰＤＲゴールド・シェア", "1326"),
        ("純銀上場信託（現物国内保管型）", "1542"),
        ("純銀上場信託", "1542"),
        ("ＷＴ白金上場投信（WisdomTree 白金）", "1674"),
        ("ＷＴ白金上場投信", "1674"),
        ("ＷＴ銅上場投信（WisdomTree 銅）", "1693"),
        ("ＷＴ銅上場投信", "1693"),
        ("東証グロース２５０ＥＴＦ", "2516"),
        ("楽天グループ", "4755"),
    ]

    print("\n" + "="*80)
    print("FUND MAPPING VERIFICATION TEST")
    print("="*80)
    print()

    passed = 0
    failed = 0

    for fund_name, expected_ticker in test_cases:
        resolved_symbol, _ = resolve_alias(fund_name, fund_name)

        if resolved_symbol == expected_ticker:
            print(f"✅ {fund_name[:50]:<50} → {resolved_symbol}")
            passed += 1
        else:
            print(f"❌ {fund_name[:50]:<50} → {resolved_symbol} (expected {expected_ticker})")
            failed += 1

    print("\n" + "="*80)
    print(f"RESULT: {passed}/{len(test_cases)} tests passed")
    if failed == 0:
        print("✅ All fund mappings working correctly!")
    else:
        print(f"❌ {failed} mappings failed")
    print("="*80 + "\n")

    return failed == 0

if __name__ == "__main__":
    success = test_all_mappings()
    exit(0 if success else 1)
