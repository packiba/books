from django.test import TestCase

from store.logic import operations


class LogicTestCase(TestCase):
    def test_plus(self):
        result = operations(6, 13, '+')
        self.assertEqual(19, result)

    def test_minus(self):
            result = operations(20, 5, '-')
            self.assertEqual(15, result)

    def test_mul(self):
            result = operations(6, 4, '*')
            self.assertEqual(24, result)


