import unittest

# You are declaring a class here and defining the functions as static since they
# have no access to the 'self' reference. However you are not explicitly telling
# the class that these are static functions. If you were to create an instance of
# this class, shit would go haywire.


class SampleMath:

    # FIXME Must add the staticmethod decorators
    @staticmethod
    def add_two_numbers(x, y):
        return x + y

    @staticmethod
    def sub_two_numbers(x, y):
        return x - y

    @staticmethod
    def second_power(x):
        return x * x

    @staticmethod
    def check_even(x):
        if x % 2 == 0:
            return True
        else:
            return False


class Test (unittest.TestCase):

    def test_even_number_for_even_method(self):
        # removed the local instances of the SampleMath class
        self.assertTrue(SampleMath.check_even(2))

    def test_odd_number_for_even_method(self):
        self.assertFalse(SampleMath.check_even(3))

    def test_power(self):
        self.assertEqual(SampleMath.second_power(-2),4)

    def test_add_two_numbers_positive(self):
        self.assertEqual(SampleMath.add_two_numbers(3, 3), 6)

    def test_add_two_numbers_negative(self):
        self.assertEqual(SampleMath.add_two_numbers(-3, -3), -6)

    @unittest.expectedFailure
    def test_make_fail(self):
        self.assertEqual(SampleMath.second_power(-2), 5)

    def test_add_two_numbers_negative_and_positive(self):
        self.assertEqual(SampleMath.add_two_numbers(-3, 5), 2)

    @unittest.skip("skipped test skip")
    def test_skip(self):
        print("this is in the skip, it shouldn't print")

    def bad_syntax(self):
        print("this shouldn't get run because it doesn't start with tests")

if __name__ == '__main__':
    unittest.main()
