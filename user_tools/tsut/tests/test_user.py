import unittest

from tsut.model import User, Visibility

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


class TestUser(unittest.TestCase):
    """Tests the User class."""

    def test_create_user(self):
        """Tests creation of a new user."""
        u = User(
            name="someuser",
            password="mysecretpwd",
            mail="myemail@company.com",
            display_name="Some User",
            created="1234",
        )

        self.assertEqual(u.principalTypeEnum, "LOCAL_USER")
        self.assertEqual(u.name, "someuser")
        self.assertEqual(u.password, "mysecretpwd")
        self.assertEqual(u.mail, "myemail@company.com")
        self.assertEqual(u.displayName, "Some User")
        self.assertEqual(u.visibility, Visibility.DEFAULT)
        self.assertEqual(u.created, "1234")

    def test_create_non_shareable_user(self):
        """Tests creation of a new user."""
        u = User(
            name="someuser",
            password="mysecretpwd",
            mail="myemail@company.com",
            display_name="Some User",
            visibility=Visibility.NON_SHAREABLE,
        )

        self.assertEqual(u.principalTypeEnum, "LOCAL_USER")
        self.assertEqual(u.name, "someuser")
        self.assertEqual(u.password, "mysecretpwd")
        self.assertEqual(u.mail, "myemail@company.com")
        self.assertEqual(u.displayName, "Some User")
        self.assertEqual(u.visibility, Visibility.NON_SHAREABLE)

    def test_user_to_json(self):
        """Tests converting a user to JSON."""
        u = User(
            name="someuser",
            password="mysecretpwd",
            mail="myemail@company.com",
            display_name="Some User",
            created="1234",
        )

        json = u.to_json()
        self.assertTrue('"principalTypeEnum":"LOCAL_USER"' in json)
        self.assertTrue('"name":"someuser"' in json)
        self.assertTrue('"password":"mysecretpwd"' in json)
        self.assertTrue('"mail":"myemail@company.com"' in json)
        self.assertTrue('"displayName":"Some User"' in json)
        self.assertTrue('"visibility":"' + Visibility.DEFAULT + '"' in json)
        self.assertTrue('"created":"' + "1234" + '"' in json)
        self.assertTrue(json[0], "{")
        self.assertTrue(json.endswith("}"))

    def test_non_shareable_user_to_json(self):
        """Tests converting a non-shareable user to JSON."""
        u = User(
            name="someuser",
            password="mysecretpwd",
            mail="myemail@company.com",
            display_name="Some User",
            visibility=Visibility.NON_SHAREABLE,
        )

        json = u.to_json()
        self.assertTrue('"principalTypeEnum":"LOCAL_USER"' in json)
        self.assertTrue('"name":"someuser"' in json)
        self.assertTrue('"password":"mysecretpwd"' in json)
        self.assertTrue('"mail":"myemail@company.com"' in json)
        self.assertTrue('"displayName":"Some User"' in json)
        self.assertTrue(
            '"visibility":"' + Visibility.NON_SHAREABLE + '"' in json
        )
        self.assertTrue(json[0], "{")
        self.assertTrue(json.endswith("}"))

    def test_blank_values_in_json(self):
        """Tests missing values are being left out of JSON"""
        u = User("user1")
        json = u.to_json()
        self.assertFalse(", ," in json)

    def test_add_groups_to_user(self):
        u = User(name="just_the_groups")

        self.assertEqual(u.groupNames, [])

        u.add_group("group 1")
        u.add_group("group 2")
        u.add_group("group 1")

        self.assertEqual(u.groupNames, ["group 1", "group 2"])


if __name__ == "__main__":
    unittest.main()
