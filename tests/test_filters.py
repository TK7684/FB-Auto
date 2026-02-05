import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.filters import is_relevant_post, is_ignored_user

def test_filters():
    # Test positive cases
    assert is_relevant_post("This is a normal post about skincare.")
    assert is_relevant_post("Promotion for new serum!")
    assert is_relevant_post("")
    
    # Test negative cases
    assert not is_relevant_post("ขายบ้าน hand 2")
    assert not is_relevant_post("#คุณก้งขายบ้าน")
    assert not is_relevant_post("มีทาวน์โฮมให้เช่า")
    
    print("All filter tests passed!")

def test_user_filters():
    # Test ignored users
    assert is_ignored_user("Treepehch Kwangkhwang")
    
    # Test allowed users
    assert not is_ignored_user("John Doe")
    assert not is_ignored_user("")
    assert not is_ignored_user(None)
    
    print("All user filter tests passed!")

if __name__ == "__main__":
    test_filters()
    test_user_filters()
