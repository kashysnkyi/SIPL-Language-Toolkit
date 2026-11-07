import pytest

from sipl.parser import SiplParser, SiplSyntaxError


VALID = [
    "begin skip end",
    "begin X := 1 end",
    "begin X := 1; Y := X + 2 end",
    "begin if X = 0 then Y := 1 else Y := 2 end",
    "begin while X > 0 do X := X - 1 end",
    "begin begin X := 1; Y := 2 end end",
    "begin X := (2 + 3) * 4 end",
    "begin X := 17 div 5; Y := 17 mod 5 end",
    "begin if not (X = 1) then skip else X := -1 end",
    "begin if X > 0 and Y > 0 or false then Z := 1 else Z := 0 end",
    "begin // comment\n X := 1 /* block comment */ end",
]

INVALID = [
    "",
    "X := 1",
    "begin X = 1 end",
    "begin X := end",
    "begin if X = 1 X := 2 else X := 3 end",
    "begin if X = 1 then X := 2 end",
    "begin while X > 0 X := X - 1 end",
    "begin X := 1 + end",
    "begin begin X := 1 end",
    "begin X := 01 end",
    "begin X := @ end",
]


@pytest.mark.parametrize("source", VALID)
def test_valid_programs(source):
    assert SiplParser().parse(source).program is not None


@pytest.mark.parametrize("source", INVALID)
def test_invalid_programs(source):
    with pytest.raises(SiplSyntaxError):
        SiplParser().parse(source)

