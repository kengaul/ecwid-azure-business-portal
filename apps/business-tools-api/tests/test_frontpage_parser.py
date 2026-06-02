from business_tools.frontpage.parser import parse_skus


def test_parse_skus_accepts_common_paste_formats():
    skus, warnings = parse_skus("AAA\nBBB,CCC\tDDD EEE", max_skus=10)

    assert skus == ["AAA", "BBB", "CCC", "DDD", "EEE"]
    assert warnings == []


def test_parse_skus_skips_duplicates_case_insensitively():
    skus, warnings = parse_skus(["ABC", "abc", "DEF"], max_skus=10)

    assert skus == ["ABC", "DEF"]
    assert [warning.code for warning in warnings] == ["duplicate"]


def test_parse_skus_enforces_max_skus():
    skus, warnings = parse_skus("A B C", max_skus=2)

    assert skus == ["A", "B"]
    assert warnings[0].code == "max_skus_exceeded"
