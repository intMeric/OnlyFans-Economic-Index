"""Test main module functionality."""

from onlyfans_economic_index.main import load_usernames_from_file


def test_load_usernames_from_nonexistent_file():
    """Test loading usernames from a file that doesn't exist."""
    usernames = load_usernames_from_file("nonexistent_file.txt")
    assert usernames == []


def test_imports():
    """Test that main module imports work correctly."""
    from onlyfans_economic_index import main
    assert hasattr(main, 'main')
    assert hasattr(main, 'load_usernames_from_file')
    assert hasattr(main, 'save_profile_snapshot')
    assert hasattr(main, 'save_all_profiles_from_file')
