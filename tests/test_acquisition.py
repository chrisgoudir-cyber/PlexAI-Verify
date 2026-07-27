from pathlib import Path
from tempfile import TemporaryDirectory
from core.acquisition.models import MissingMovie
from core.acquisition.wishlist import WishlistRepository

def test_wishlist_add_and_duplicate():
    with TemporaryDirectory() as tmp:
        repo = WishlistRepository(Path(tmp) / "test.db")
        movie = MissingMovie("Alien 3", 1992, "Alien")
        assert repo.add(movie) is True
        assert repo.add(movie) is False
        assert len(repo.list_all()) == 1

def test_display_title():
    assert MissingMovie("Rocky V", 1990).display_title == "Rocky V (1990)"
    assert MissingMovie("Sans année").display_title == "Sans année"
