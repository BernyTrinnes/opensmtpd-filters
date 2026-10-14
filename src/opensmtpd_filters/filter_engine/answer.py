from enum import Enum, unique


@unique
class Answer(Enum):
    """ Answer verbs for the protocol supported by the OpenSMTPd filter API. """
    
    UNKNOWN = "unknown"
    """ An unknown/invalid answer. """
    
    REGISTER = "register"
    """ The answer verb used to register the stream, subsystem and event that should be handled.
    `External documentation. <https://man.openbsd.org/smtpd-filters#PROTOCOL>`__"""
    
    FILTER_RESULT = "filter-result"
    """ The answer verb for all filter phases, except the data-line phase.
    `External documentation. <https://man.openbsd.org/smtpd-filters#FILTER_REQUESTS>`__"""
    
    FILTER_DATALINE = "filter-dataline"
    """ The answer verb for the data-line phase.
    `External documentation. <https://man.openbsd.org/smtpd-filters#FILTER_REQUESTS>`__"""
    
    def __bool__(self) -> bool:
        """
        Implement truth value testing for this enumeration.
        
        :return: ``False`` if the enumeration member is ``Answer.UNKNOWN``, ``True`` for all other enumeration members.
        :rtype: bool
        """
        
        return self is not Answer.UNKNOWN
    
    def __str__(self) -> str:
        """
        Retrieve the string representation of this answer verb.
        
        :return: The string which represents this answer verb.
        :rtype: str
        """
        
        return str(self.value)
    
    def __repr__(self) -> str:
        """
        Retrieve the representation of this answer verb.
        
        :return: The representation of this answer verb.
        :rtype: str
        """
        
        return f"{self.__class__.__name__}.{self.name}"
    
    @classmethod
    def _missing_(cls, value: object) -> 'Answer':
        """
        A method for looking up values in ``Answer``. The value will be searched case-insensitive.
        
        :param value: The case-insensitive value to search for.
        :type value: object
        :return: The matched answer verb, or ``Answer.UNKNOWN`` if the value is not a string or does not match a defined
        answer verb.
        :rtype: Answer
        """
        
        if not isinstance(value, str):
            return Answer.UNKNOWN
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return Answer.UNKNOWN
