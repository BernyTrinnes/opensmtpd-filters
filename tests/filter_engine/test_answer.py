from opensmtpd_filters.filter_engine import Answer


class TestAnswer:
    """ Tests for the enumeration ``Answer``. """
    
    def test_when_bool_then_correct_value_returned(self) -> None:
        assert not bool(Answer.UNKNOWN)
        assert bool(Answer.REGISTER)
    
    def test_when_str_then_correct_string_returned(self) -> None:
        for answer in Answer:
            assert str(answer) == answer.name.lower().replace("_", "-")
    
    def test_when_repr_then_correct_representation_returned(self) -> None:
        for answer in Answer:
            assert repr(answer) == f"Answer.{answer.name}"
    
    def test_when_missing_then_correct_member_returned(self) -> None:
        assert Answer("filter-dataline") == Answer.FILTER_DATALINE
        assert Answer("FILTER-RESULT") == Answer.FILTER_RESULT
        assert Answer("answer") == Answer.UNKNOWN
        assert Answer(5) == Answer.UNKNOWN
