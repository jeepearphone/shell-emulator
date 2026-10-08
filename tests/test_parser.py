"""Тесты разбора командной строки."""

import os
import unittest

from commands import parse, ShellError


class ParseTest(unittest.TestCase):
    """Проверки функции parse."""

    def test_split_words(self):
        """Строка делится на слова по пробелам."""
        self.assertEqual(parse("ls -l /home"), ["ls", "-l", "/home"])

    def test_quotes(self):
        """Кавычки объединяют слова и снимаются."""
        self.assertEqual(parse('cd "/home/user"'), ["cd", "/home/user"])

    def test_env_variable(self):
        """Переменные окружения ОС раскрываются."""
        os.environ["EMU_TEST_DIR"] = "/home/user"
        self.assertEqual(parse("cd $EMU_TEST_DIR"), ["cd", "/home/user"])

    def test_empty_line(self):
        """Пустая строка даёт пустой список."""
        self.assertEqual(parse("   "), [])

    def test_unclosed_quote(self):
        """Незакрытая кавычка вызывает ошибку."""
        with self.assertRaises(ShellError):
            parse('ls "unclosed')


if __name__ == "__main__":
    unittest.main()