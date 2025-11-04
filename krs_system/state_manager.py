"""
KRS State Management Module
Manages state transitions for the Course Registration System (KRS)
"""
from krs_system.enums import KRSStatusEnum as KRSStatus  # Use shared enum class


def transition(current_status: KRSStatus, action: str) -> KRSStatus:
    """
    Transition function to handle valid state transitions for KRS
    
    Args:
        current_status: Current KRSStatus
        action: Action to perform
        
    Returns:
        New KRSStatus after transition
        
    Raises:
        ValueError: If the transition is invalid
    """
    # Define valid transitions
    valid_transitions = {
        (KRSStatus.DRAFT, "submit"): KRSStatus.SUBMITTED,
        (KRSStatus.SUBMITTED, "approve"): KRSStatus.APPROVED,
        (KRSStatus.SUBMITTED, "reject"): KRSStatus.REVISION,
        (KRSStatus.REVISION, "resubmit"): KRSStatus.SUBMITTED,
    }
    
    # Check if the transition is valid
    transition_key = (current_status, action)
    if transition_key in valid_transitions:
        return valid_transitions[transition_key]
    else:
        raise ValueError(f"Transisi tidak valid dari {current_status.value} dengan aksi {action}")


if __name__ == "__main__":
    # Test the transition function
    print("Testing KRS state transitions...")
    
    # Test valid transitions
    try:
        # DRAFT -> SUBMITTED
        current = KRSStatus.DRAFT
        new_status = transition(current, "submit")
        print(f"SUCCESS: {current.value} -> submit -> {new_status.value}")
        
        # SUBMITTED -> APPROVED
        current = new_status
        new_status = transition(current, "approve")
        print(f"SUCCESS: {current.value} -> approve -> {new_status.value}")
        
        # Start over for testing another path
        current = KRSStatus.DRAFT
        current = transition(current, "submit")
        # SUBMITTED -> REVISION
        new_status = transition(current, "reject")
        print(f"SUCCESS: {current.value} -> reject -> {new_status.value}")
        
        # REVISION -> SUBMITTED
        current = new_status
        new_status = transition(current, "resubmit")
        print(f"SUCCESS: {current.value} -> resubmit -> {new_status.value}")
        
        print("All valid transitions work correctly!")
        
    except ValueError as e:
        print(f"ERROR: Unexpected error: {e}")
    
    # Test invalid transitions
    print("\nTesting invalid transitions...")
    try:
        transition(KRSStatus.DRAFT, "approve")  # Invalid: DRAFT cannot be approved directly
        print("ERROR: This should have failed!")
    except ValueError as e:
        print(f"SUCCESS: Correctly caught invalid transition: {e}")
    
    try:
        transition(KRSStatus.APPROVED, "reject")  # Invalid: APPROVED cannot be rejected
        print("ERROR: This should have failed!")
    except ValueError as e:
        print(f"SUCCESS: Correctly caught invalid transition: {e}")