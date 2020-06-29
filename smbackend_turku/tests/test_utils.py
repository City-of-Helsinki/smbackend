from smbackend_turku.importers.utils import convert_code_to_int


def test_convert_code_to_int():
    code_1 = '1_13'
    code_2 = '11_3'
    assert convert_code_to_int(code_1) == convert_code_to_int(code_1)
    assert convert_code_to_int(code_1) != convert_code_to_int(code_2)
