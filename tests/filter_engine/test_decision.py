import pytest

from opensmtpd_filters.filter_engine import Decision, FilterEngineException, NegativeReturnCode


class TestDecision:
    """ Tests for the enumeration ``Decision``. """
    
    def test_when_bool_then_correct_value_returned(self) -> None:
        assert not bool(Decision.UNKNOWN)
        assert bool(Decision.JUNK)
    
    def test_when_str_then_correct_string_returned(self) -> None:
        for decision in Decision:
            assert str(decision) == decision.name.lower().replace("_", "-")
    
    def test_when_repr_then_correct_representation_returned(self) -> None:
        for decision in Decision:
            assert repr(decision) == f"Decision.{decision.name}"
    
    def test_when_missing_then_correct_member_returned(self) -> None:
        assert Decision("rewrite") == Decision.REWRITE
        assert Decision("REWRITE") == Decision.REWRITE
        assert Decision("decision") == Decision.UNKNOWN
        assert Decision(5) == Decision.UNKNOWN
    
    @pytest.mark.parametrize("decision", [
        Decision.REJECT, Decision.DISCONNECT, Decision.REWRITE, Decision.REPORT
    ])
    def test_when_decision_and_decision_has_param_and_none_given_then_exception(self, decision: Decision) -> None:
        with pytest.raises(FilterEngineException) as context:
            Decision.decision(decision)
        
        assert isinstance(context.value, FilterEngineException)
        assert str(context.value) == "To build the message this decision needs either a return code or a message."
    
    @pytest.mark.parametrize("decision, return_code, message, expected_result", [
        (Decision.PROCEED, None, None, "proceed"),
        (Decision.JUNK, None, None, "junk"),
        (Decision.REJECT, None, "message", "reject|message"),
        (Decision.DISCONNECT, None, "message", "disconnect|message"),
        (Decision.REWRITE, None, "message", "rewrite|message"),
        (Decision.REPORT, None, "message", "report|message"),
        (Decision.PROCEED, None, "message", "proceed"),
        (Decision.JUNK, None, "message", "junk"),
        (Decision.REJECT, NegativeReturnCode.E_502, None, "reject|502 Command not implemented"),
        (Decision.DISCONNECT, NegativeReturnCode.E_502, None, "disconnect|502 Command not implemented"),
        (Decision.REWRITE, NegativeReturnCode.E_502, None, "rewrite|502 Command not implemented"),
        (Decision.REPORT, NegativeReturnCode.E_502, None, "report|502 Command not implemented"),
        (Decision.PROCEED, NegativeReturnCode.E_502, None, "proceed"),
        (Decision.JUNK, NegativeReturnCode.E_502, None, "junk"),
        (Decision.REJECT, NegativeReturnCode.E_502, "message", "reject|502 message"),
        (Decision.DISCONNECT, NegativeReturnCode.E_502, "message", "disconnect|502 message"),
        (Decision.REWRITE, NegativeReturnCode.E_502, "message", "rewrite|message"),
        (Decision.REPORT, NegativeReturnCode.E_502, "message", "report|message"),
        (Decision.PROCEED, NegativeReturnCode.E_502, "message", "proceed"),
        (Decision.JUNK, NegativeReturnCode.E_502, "message", "junk"),
        (Decision.REJECT, None, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"), "reject|501 message"),
        (Decision.DISCONNECT, None, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"),
         "disconnect|501 message"),
        (Decision.REWRITE, None, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"),
         "rewrite|501 message"),
        (Decision.REPORT, None, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"), "report|501 message"),
        (Decision.PROCEED, None, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"), "proceed"),
        (Decision.JUNK, None, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"), "junk"),
        (Decision.REJECT, NegativeReturnCode.E_502, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"),
         "reject|502 501 message"),
        (Decision.DISCONNECT, NegativeReturnCode.E_502, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"),
         "disconnect|502 501 message"),
        (Decision.REWRITE, NegativeReturnCode.E_502, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"),
         "rewrite|501 message"),
        (Decision.REPORT, NegativeReturnCode.E_502, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"),
         "report|501 message"),
        (Decision.PROCEED, NegativeReturnCode.E_502, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"),
         "proceed"),
        (Decision.JUNK, NegativeReturnCode.E_502, NegativeReturnCode.message(NegativeReturnCode.E_501, "message"),
         "junk")
    ])
    def test_when_decision_then_correct_string_returned(self, decision: Decision,
            return_code: NegativeReturnCode | None,
            message: str | None, expected_result: str) -> None:
        assert str(Decision.decision(decision, return_code, message)) == expected_result


class TestNegativeReturnCode:
    """ Tests for the enumeration ``NegativeReturnCode``. """
    
    def test_when_str_then_correct_string_returned(self) -> None:
        for return_code in NegativeReturnCode:
            assert str(return_code).startswith(f"{return_code.value} ")
    
    def test_when_custom_message_then_correct_string_returned(self) -> None:
        for return_code in NegativeReturnCode:
            assert NegativeReturnCode.message(return_code, "custom message") == f"{return_code.value} custom message"
    
    def test_when_repr_then_correct_representation_returned(self) -> None:
        for return_code in NegativeReturnCode:
            assert repr(return_code) == f"NegativeReturnCode.{return_code.name}"
