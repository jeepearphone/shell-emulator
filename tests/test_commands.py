"""Тесты команд эмулятора."""

import os
import unittest

from tests.helpers import make_sample_dir, sample_path
from commands import execute, ExitShell, Session, ShellError
from vfs import VFS


class CommandsTest(unittest.TestCase):
    """Проверки команд ls, cd, pwd, cat, rm, exit, vfs-info, vfs-init."""

    def setUp(self):
        """Загружает тестовую VFS; подтверждение vfs-init всегда да."""
        self.temp = make_sample_dir()
        vfs = VFS()
        vfs.load(sample_path(self.temp))
        self.answer = True
        self.session = Session(vfs, lambda question: self.answer)

    def tearDown(self):
        """Удаляет тестовую папку."""
        self.temp.cleanup()

    def run_cmd(self, line):
        """Выполняет команду в тестовой сессии."""
        return execute(line, self.session)

    def test_unknown_command(self):
        """Неизвестная команда вызывает ошибку."""
        with self.assertRaises(ShellError):
            self.run_cmd("unknown_cmd arg")

    def test_ls(self):
        """Команда ls выводит содержимое папки, папки отмечены /."""
        self.assertEqual(self.run_cmd("ls"), "etc/  home/  readme.txt")

    def test_ls_long(self):
        """Команда ls -l выводит тип и размер."""
        self.assertIn("-       12  readme.txt", self.run_cmd("ls -l"))

    def test_ls_errors(self):
        """Команда ls сообщает о неверном флаге и лишних аргументах."""
        for line in ("ls -x", "ls a b", "ls /nosuch"):
            with self.assertRaises(ShellError):
                self.run_cmd(line)

    def test_cd_and_pwd(self):
        """Команда cd меняет текущую папку, pwd её показывает."""
        self.run_cmd("cd home/user")
        self.assertEqual(self.run_cmd("pwd"), "/home/user")
        self.run_cmd("cd ../../etc")
        self.assertEqual(self.run_cmd("pwd"), "/etc")
        self.run_cmd("cd")
        self.assertEqual(self.run_cmd("pwd"), "/")

    def test_cd_errors(self):
        """Команда cd сообщает об ошибках и не меняет папку."""
        for line in ("cd /nosuch", "cd readme.txt", "cd a b"):
            with self.assertRaises(ShellError):
                self.run_cmd(line)
        self.assertEqual(self.run_cmd("pwd"), "/")

    def test_cat(self):
        """Команда cat выводит один и несколько файлов."""
        self.assertEqual(self.run_cmd("cat readme.txt"), "root readme")
        text = self.run_cmd("cat etc/config.txt home/user/notes.txt")
        self.assertEqual(text, "mode=test\nmy notes")

    def test_cat_errors(self):
        """Команда cat сообщает об отсутствии файла и о папке."""
        for line in ("cat", "cat /nosuch.txt", "cat home"):
            with self.assertRaises(ShellError):
                self.run_cmd(line)

    def test_rm_file_only_in_memory(self):
        """Команда rm удаляет файл из VFS, но не с диска."""
        self.run_cmd("rm /home/user/notes.txt")
        self.assertEqual(self.run_cmd("ls /home/user"), "docs/")
        disk = os.path.join(sample_path(self.temp), "home", "user",
                            "notes.txt")
        self.assertTrue(os.path.exists(disk))

    def test_rm_recursive(self):
        """Команда rm -r удаляет папку, без -r это ошибка."""
        with self.assertRaises(ShellError):
            self.run_cmd("rm etc")
        self.run_cmd("rm -r etc")
        self.assertEqual(self.run_cmd("ls"), "home/  readme.txt")

    def test_rm_force(self):
        """Команда rm -f молчит об отсутствующем файле."""
        self.assertEqual(self.run_cmd("rm -f /nosuch.txt"), "")
        with self.assertRaises(ShellError):
            self.run_cmd("rm /nosuch.txt")

    def test_rm_protected(self):
        """Нельзя удалить корень, текущую папку и её родителей."""
        self.run_cmd("cd /home/user")
        for line in ("rm -r /", "rm -r .", "rm -r ..", "rm", "rm -x a"):
            with self.assertRaises(ShellError):
                self.run_cmd(line)

    def test_exit(self):
        """Команда exit завершает работу, с аргументом это ошибка."""
        with self.assertRaises(ExitShell):
            self.run_cmd("exit")
        with self.assertRaises(ShellError):
            self.run_cmd("exit now")

    def test_vfs_info(self):
        """Команда vfs-info выводит имя и дерево VFS."""
        info = self.run_cmd("vfs-info")
        self.assertIn("name:   deep", info)
        self.assertIn("todo.txt (10 bytes)", info)

    def test_vfs_init_cancel(self):
        """При отказе vfs-init ничего не меняет."""
        self.answer = False
        self.run_cmd("vfs-init")
        self.assertIn("readme.txt", self.run_cmd("ls"))

    def test_vfs_init(self):
        """Команда vfs-init заменяет VFS на пустую и очищает папку."""
        self.run_cmd("cd /home")
        self.run_cmd("vfs-init")
        self.assertEqual(self.run_cmd("ls"), "")
        self.assertEqual(self.run_cmd("pwd"), "/")
        self.assertEqual(os.listdir(sample_path(self.temp)), [])


if __name__ == "__main__":
    unittest.main()