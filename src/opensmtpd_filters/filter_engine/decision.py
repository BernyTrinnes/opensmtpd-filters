from enum import Enum, unique


@unique
class Decision(Enum):
    """ Decisions which can be taken during every filtering phase, except data-line. """
    
    UNKNOWN = "unknown"
    """ An unknown/invalid decision. """
    
    PROCEED = "proceed"
    """ No action is taken, session or transaction may be passed to the next filter. `External documentation.
    <https://man.openbsd.org/smtpd-filters#proceed>`__"""
    
    JUNK = "junk"
    """ The session or transaction is marked as spam. `External documentation.
    <https://man.openbsd.org/smtpd-filters#junk>`__"""
    
    REJECT = ("reject", True, True)
    """ The command is rejected with the message given in the parameter. `External documentation.
    <https://man.openbsd.org/smtpd-filters#reject>`__"""
    
    DISCONNECT = ("disconnect", True, True)
    """ The client is disconnected with the message given in the parameter. `External documentation.
    <https://man.openbsd.org/smtpd-filters#disconnect>`__"""
    
    REWRITE = ("rewrite", True)
    """ The command parameter is rewritten. `External documentation.
    <https://man.openbsd.org/smtpd-filters#rewrite>`__"""
    
    REPORT = ("report", True)
    """ Generates a report with a given parameter for this filter. `External documentation.
    <https://man.openbsd.org/smtpd-filters#report>`__"""
    
    def __new__(cls, value: str, has_param: bool = False, is_param_error: bool = False) -> 'Decision':
        """
        Create a new decision enumeration member.
        
        :param value: The value of the decision, as it is used in the filter response.
        :type value: str
        :param has_param: ``True`` if this decision must also specify a parameter, ``False`` otherwise.
        :type has_param: bool
        :param is_param_error: ``True`` if the parameter is an error message, ``False`` otherwise.
        :type is_param_error: bool
        :return: The newly created decision enum member.
        :rtype: Decision
        """
        
        decision = object.__new__(cls)
        decision._value_ = value
        decision.has_param = has_param
        decision.is_param_error = is_param_error
        return decision
    
    def __bool__(self) -> bool:
        """
        Implement truth value testing for this enumeration.
        
        :return: ``False`` if the enumeration member is ``Decision.UNKNOWN``, ``True`` for all other enumeration
        members.
        :rtype: bool
        """
        
        return self is not Decision.UNKNOWN
    
    def __str__(self) -> str:
        """
        Retrieve the string representation of this decision.
        
        :return: The string which represents this decision.
        :rtype: str
        """
        
        return str(self.value)
    
    def __repr__(self) -> str:
        """
        Retrieve the representation of this decision.
        
        :return: The representation of this decision.
        :rtype: str
        """
        
        return f"{self.__class__.__name__}.{self.name}"
    
    @classmethod
    def _missing_(cls, value: object) -> 'Decision':
        """
        A method for looking up values in ``Decision``. The value will be searched case-insensitive.
        
        :param value: The case-insensitive value to search for.
        :type value: object
        :return: The matched decision, or ``Decision.UNKNOWN`` if the value is not a string or does not match a
        defined decision.
        :rtype: Decision
        """
        
        if not isinstance(value, str):
            return Decision.UNKNOWN
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return Decision.UNKNOWN
