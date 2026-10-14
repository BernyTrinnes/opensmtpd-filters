from opensmtpd_filters.filter_engine import Subsystem


class TestSubsystem:
    """ Tests for the class ``Subsystem``. """
    
    def test_when_bool_then_correct_value_returned(self) -> None:
        assert not bool(Subsystem.UNKNOWN)
        assert bool(Subsystem.SMTP_IN)
    
    def test_when_str_called_then_correct_string_returned(self) -> None:
        for subsystem in Subsystem:
            assert subsystem.name.lower().replace("_", "-") == str(subsystem)
    
    def test_when_repr_called_then_correct_representation_returned(self) -> None:
        for subsystem in Subsystem:
            assert repr(subsystem) == f"Subsystem.{subsystem.name}"
    
    def test_when_missing_called_then_correct_member_returned(self) -> None:
        assert Subsystem("smtp-in") == Subsystem.SMTP_IN
        assert Subsystem("SMTP-IN") == Subsystem.SMTP_IN
        assert Subsystem("subsystem") == Subsystem.UNKNOWN
        assert Subsystem(5) == Subsystem.UNKNOWN
