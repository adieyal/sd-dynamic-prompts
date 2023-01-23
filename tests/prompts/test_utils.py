from prompts.utils import slugify


class TestSlugify:
    def test_identity(self):
        assert slugify("foo") == "foo"

    def test_strip(self):
        assert slugify(" foo ") == "foo"

    def test_spaces(self):
        assert slugify("foo bar") == "foo-bar"

    def test_dashes(self):
        assert slugify("foo--bar") == "foo-bar"

    def test_unicode(self):
        assert slugify("föö") == "foo"

    def test_unicode_allow(self):
        assert slugify("föö", allow_unicode=True) == "föö"

    def test_non_ascii(self):
        assert slugify("föö", allow_unicode=False) == "foo"

    def test_max_length(self):
        assert len(slugify("foo" * 100)) == 50
        assert len(slugify("foo" * 100, max_length=25)) == 25



