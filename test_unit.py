import unittest

from app import *
from main import *

class FlaskTestCase(unittest.TestCase):

    def test_app(self):
        response = app.test_client(self)
        response = response.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()