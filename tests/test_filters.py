import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.filters import is_relevant_post

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

if __name__ == "__main__":
    test_filters()
