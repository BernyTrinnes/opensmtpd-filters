from opensmtpd_filters.filter_engine import Answer

class TestAnswer:
    """ Tests for the enumeration ``Answer``. """
    
    def test_when_bool_then_correct_value_returned(self) -> None:
        assert not bool(Answer.UNKNOWN)
        assert bool(Answer.REGISTER)
    
    def test_when_str_then_correct_string_returned(self) -> None:
        for answer in Answer:
            assert answer.name.lower().replace("_", "-") == str(answer)
    
    def test_when_repr_then_correct_representation_returned(self) -> None:
        for answer in Answer:
            assert f"Answer.{answer.name}" == repr(answer)
    
    def test_when_missing_then_correct_member_returned(self) -> None:
        assert Answer.FILTER_DATALINE == Answer("filter-dataline")
        assert Answer.FILTER_RESULT == Answer("FILTER-RESULT")
        assert Answer.UNKNOWN == Answer("answer")
        assert Answer.UNKNOWN == Answer(5)
