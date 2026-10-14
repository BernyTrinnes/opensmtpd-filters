from enum import Enum, unique


@unique
class Subsystem(Enum):
    """ Subsystems supported by the OpenSMTPd filter API. """
    
    UNKNOWN = "unknown"
    """ An unknown/invalid subsystem. """
    
    SMTP_IN = "smtp-in"
    """ The smtp_in subsystem. At this time, this is the only supported subsystem. """
    
    def __bool__(self) -> bool:
        """
        Implement truth value testing for this enumeration.
        
        :return: ``False`` if the enumeration member is ``Subsystem.UNKNOWN``, ``True`` for all other enumeration
        members.
        :rtype: bool
        """
        
        return self is not Subsystem.UNKNOWN
    
    def __str__(self) -> str:
        """
        Retrieve the string representation of this subsystem.
        
        :return: The string which represents this subsystem.
        :rtype: str
        """
        
        return str(self.value)
    
    def __repr__(self) -> str:
        """
        Retrieve the representation of this subsystem.
        
        :return: The representation of this subsystem.
        :rtype: str
        """
        
        return f"{self.__class__.__name__}.{self.name}"
    
    @classmethod
    def _missing_(cls, value: object) -> 'Subsystem':
        """
        A method for looking up values in ``Subsystem``. The value will be searched case-insensitive.
        
        :param value: The case-insensitive value to search for.
        :type value: object
        :return: The matched subsystem, or ``Subsystem.UNKNOWN`` if the value is not a string or does not match a
        defined subsystem.
        :rtype: Subsystem
        """
        
        if not isinstance(value, str):
            return Subsystem.UNKNOWN
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return Subsystem.UNKNOWN
