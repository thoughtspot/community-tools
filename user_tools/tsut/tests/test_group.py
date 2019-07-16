import unittest

from tsut.model import Group, Visibility

"""
Copyright 2018 ThoughtSpot

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


class TestGroup(unittest.TestCase):
    """Tests the Group class."""

    def test_create_group(self):
        """Tests creation of a group."""
        g = Group(name="somegroup", display_name="Some Group",
                  description="Just some average group")

        self.assertEquals(g.principalTypeEnum, "LOCAL_GROUP")
        self.assertEquals(g.name, "somegroup")
        self.assertEquals(g.displayName, "Some Group")
        self.assertEquals(g.description, "Just some average group")
        self.assertEqual(g.visibility, Visibility.DEFAULT)

    def test_create_non_shareable_group(self):
        """Tests creation of a group with visibility of non-shareable."""
        g = Group(name="somegroup", display_name="Some Group",
                  description="Just some average group", visibility=Visibility.NON_SHAREABLE)

        self.assertEquals(g.principalTypeEnum, "LOCAL_GROUP")
        self.assertEquals(g.name, "somegroup")
        self.assertEquals(g.displayName, "Some Group")
        self.assertEquals(g.description, "Just some average group")
        self.assertEqual(g.visibility, Visibility.NON_SHAREABLE)

    def test_group_to_json(self):
        """Tests converting a group to JSON."""
        g = Group(name="somegroup", display_name="Some Group",
                  description="Just some average group")

        json = g.to_json()
        self.assertTrue('"principalTypeEnum":"LOCAL_GROUP"' in json)
        self.assertTrue('"name":"somegroup"' in json)
        self.assertTrue('"displayName":"Some Group"' in json)
        self.assertTrue('"description":"Just some average group"' in json)
        self.assertTrue('"visibility":"' + Visibility.DEFAULT + '"' in json)
        self.assertTrue(json[0], "{")
        self.assertTrue(json.endswith("}"))

    def test_non_shareable_group_to_json(self):
        """Tests converting a group to JSON."""
        g = Group(name="somegroup", display_name="Some Group",
                  description="Just some average group", visibility=Visibility.NON_SHAREABLE)

        json = g.to_json()
        self.assertTrue('"principalTypeEnum":"LOCAL_GROUP"' in json)
        self.assertTrue('"name":"somegroup"' in json)
        self.assertTrue('"displayName":"Some Group"' in json)
        self.assertTrue('"description":"Just some average group"' in json)
        self.assertTrue('"visibility":"' + Visibility.NON_SHAREABLE + '"' in json)
        self.assertTrue(json[0], "{")
        self.assertTrue(json.endswith("}"))

    def test_blank_values_in_json(self):
        """Tests missing values are being left out of JSON"""
        g = Group("group1")
        json = g.to_json()
        self.assertFalse(", ," in json)

    def test_add_groups_to_group(self):
        """Tests adding parent groups."""
        u = Group(name="just_the_groups")

        self.assertEquals(u.groupNames, [])

        u.add_group("group 1")
        u.add_group("group 2")
        u.add_group("group 1")

        self.assertEquals(u.groupNames, ["group 1", "group 2"])


if __name__ == '__main__':
    unittest.main()
