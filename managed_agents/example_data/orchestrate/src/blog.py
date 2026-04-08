from datetime import date

from .url_utils import normalize_path, slugify


def generate_post_url(title: str, published: date) -> str:
    slug = slugify(title)
    return normalize_path(f"/blog/{published.year}/{published.month:02d}/{slug}")


def generate_author_url(name: str) -> str:
    return normalize_path(f"/authors/{slugify(name)}")
