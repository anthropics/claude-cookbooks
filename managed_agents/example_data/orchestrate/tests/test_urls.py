from datetime import date

from src.blog import generate_author_url, generate_post_url
from src.url_utils import slugify


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_unicode():
    assert slugify("Café Culture") == "cafe-culture"
    assert slugify("Naïve Résumé") == "naive-resume"


def test_slugify_special_chars():
    assert slugify("C++ & Python!") == "c-python"


def test_post_url_unicode():
    url = generate_post_url("Café Culture", date(2026, 3, 15))
    assert url == "/blog/2026/03/cafe-culture"


def test_author_url_unicode():
    assert generate_author_url("François Müller") == "/authors/francois-muller"


def test_normalize_path():
    from src.url_utils import normalize_path

    assert normalize_path("//blog///post") == "/blog/post"
