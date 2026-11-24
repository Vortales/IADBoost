# -*- coding: utf-8 -*-
"""Расположение и сохранность исходников после организации репозитория."""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Суммы зафиксированы до перемещения. Имя файла внутри каждой папки сохранено.
MOVED_SOURCES = (
    (
        "Темы.7z",
        "Законодательная база/Исходные данные/Темы.7z",
        "5ca4045998cc648a123f2c6035254eb5a68e0a761a36f0b6b13b24a803d9d46e",
    ),
    (
        "Законопроекты после правок.7z",
        "Архив/Исходные архивы/Законопроекты после правок.7z",
        "6dbb2c159ae8a624840befc65360afd51e7c5b7a6c8abcf9fedcf5901e580f58",
    ),
    (
        "Предложения.txt",
        "Аналитика/Предложения по адвокатуре/Исходные данные/Предложения.txt",
        "1393284e169d6ef7d384183f12940a3fe19fdf7b498a5742050e937cccee1b97",
    ),
    (
        "Аналитика/IAD.txt",
        "Аналитика/IAD — статус при задержании/Исходные данные/IAD.txt",
        "7307b22b8d9d398a386936416597577ef1f4167b796f49cac27a6de54f0a8130",
    ),
    (
        "Ответ на вопрос.7z",
        "Компромат на Jonny Zakonov/Иск № 105 и связанные дела/03 Исходные ответы/Ответ на вопрос.7z",
        "cce8699f42285d4d12970193f396555787fb90e6ce3c03a6d37584ac69dcea20",
    ),
    (
        "Компромат на Jonny Zakonov/imageeec74a2eea4b5124.png",
        "Компромат на Jonny Zakonov/Иск № 105 и связанные дела/01 Определение № 105/imageeec74a2eea4b5124.png",
        "808dfc0f49ed04d03addec47bb5f2c821daa3798b6ea9a0db1df9517ed13da21",
    ),
    (
        "Компромат на Jonny Zakonov/IZOBRAZENIE_2026-11-23_155611554.png",
        "Компромат на Jonny Zakonov/Иск № 105 и связанные дела/01 Определение № 105/IZOBRAZENIE_2026-11-23_155611554.png",
        "596db208d61f19b98bc1a988f0915d2fc2e915d6b56cdec6429a2bc01f780bd0",
    ),
    (
        "Компромат на Jonny Zakonov/imagef832ebf6a660e4d6.png",
        "Компромат на Jonny Zakonov/Иск № 105 и связанные дела/02 Определение № 105-1/imagef832ebf6a660e4d6.png",
        "db7497022649d74a1246513e8655c11c6356c71aeefde90faec33266880966e6",
    ),
    (
        "Компромат на Jonny Zakonov/IZOBRAZENIE_2026-11-23_155719711.png",
        "Компромат на Jonny Zakonov/Иск № 105 и связанные дела/02 Определение № 105-1/IZOBRAZENIE_2026-11-23_155719711.png",
        "39f38a044f934e9ed36f3421f8030eebcb86ef26ff119fe60e8ee2d841d979df",
    ),
    (
        "Компромат на Jonny Zakonov/IZOBRAZENIE_2026-11-23_155725115.png",
        "Компромат на Jonny Zakonov/Иск № 105 и связанные дела/02 Определение № 105-1/IZOBRAZENIE_2026-11-23_155725115.png",
        "14622fe2357abd7f7af0ca0e474c5562cdf2fc8ddee3982b2c814daafbb18054",
    ),
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RepositoryOrganizationTests(unittest.TestCase):
    def test_sources_moved_without_modification_or_old_duplicates(self):
        for original, destination, expected in MOVED_SOURCES:
            with self.subTest(source=original):
                self.assertFalse((ROOT / original).exists())
                path = ROOT / destination
                self.assertTrue(path.is_file(), destination)
                self.assertEqual(sha256(path), expected)

    def test_legislative_snapshot_was_not_replaced(self):
        manifest = ROOT / "Законодательная база/SHA256SUMS.txt"
        self.assertEqual(sha256(manifest),
                         "6530f0143278c11f01d4ff4192df4f8c737dadb0de7762211927dabfe46876eb")


if __name__ == "__main__":
    unittest.main()
