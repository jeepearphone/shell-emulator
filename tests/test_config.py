"""Тесты чтения параметров командной строки и XML-файла."""

import os
import tempfile
import unittest

from config import load_settings

GOOD_XML = (
    "<config><vfs_path>from_file</vfs_path>"
    "<startup_script>script_from_file.txt</startup_script></config>"
)


class ConfigTest(unittest.TestCase):
    """Проверки функции load_settings."""

    def setUp(self):
        """Создаёт временную папку для XML-файлов."""
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Удаляет временную папку."""
        self.temp.cleanup()

    def write(self, name, text):
        """Записывает файл во временную папку и возвращает путь к нему."""
        path = os.path.join(self.temp.name, name)
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def test_no_parameters(self):
        """Без параметров все значения не заданы."""
        settings, error = load_settings([])
        self.assertIsNone(error)
        self.assertIsNone(settings["vfs"])
        self.assertIsNone(settings["script"])

    def test_values_from_file(self):
        """Значения берутся из XML-файла."""
        path = self.write("good.xml", GOOD_XML)
        settings, error = load_settings(["--config", path])
        self.assertIsNone(error)
        self.assertEqual(settings["vfs"], "from_file")
        self.assertEqual(settings["script"], "script_from_file.txt")

    def test_cli_has_priority(self):
        """Командная строка важнее файла."""
        path = self.write("good.xml", GOOD_XML)
        settings, _ = load_settings(["--config", path, "--vfs", "cli"])
        self.assertEqual(settings["vfs"], "cli")
        self.assertEqual(settings["script"], "script_from_file.txt")

    def test_missing_file(self):
        """Отсутствующий файл даёт сообщение об ошибке."""
        _, error = load_settings(["--config", "no_such.xml"])
        self.assertIn("not found", error)

    def test_broken_xml(self):
        """Неверный XML даёт сообщение об ошибке."""
        path = self.write("bad.xml", "<config><vfs_path>x</config>")
        _, error = load_settings(["--config", path])
        self.assertIn("invalid XML", error)

    def test_wrong_root(self):
        """Неверный корневой элемент даёт сообщение об ошибке."""
        path = self.write("root.xml", "<settings></settings>")
        _, error = load_settings(["--config", path])
        self.assertIn("root element", error)


if __name__ == "__main__":
    unittest.main()