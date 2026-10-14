from opensmtpd_filters.filter_engine import Decision


class TestDecision:
    """ Tests for the enumeration ``Decision``. """
    
    def test_when_bool_then_correct_value_returned(self) -> None:
        assert not bool(Decision.UNKNOWN)
        assert bool(Decision.JUNK)
    
    def test_when_str_then_correct_string_returned(self) -> None:
        for decision in Decision:
            assert decision.name.lower().replace("_", "-") == str(decision)
    
    def test_when_repr_then_correct_representation_returned(self) -> None:
        for decision in Decision:
            assert f"Decision.{decision.name}" == repr(decision)
    
    def test_when_missing_then_correct_member_returned(self) -> None:
        assert Decision.REWRITE == Decision("rewrite")
        assert Decision.REWRITE == Decision("REWRITE")
        assert Decision.UNKNOWN == Decision("decision")
        assert Decision.UNKNOWN == Decision(5)
