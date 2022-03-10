# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime
from os import walk, makedirs, remove, path
from shutil import rmtree

import demoji
import flag
from xlrd import open_workbook
from xlwt import Workbook

if not demoji.last_downloaded_timestamp():
    demoji.download_codes()

EXTRA_WORDS = []


def get_extra_words():
    """
    Функция получения списка EXTRA_WORDS
    из файла extra-words.xls

    Файл должен находится в директории
    bot.py и соответствующе заполнен
    """
    global EXTRA_WORDS
    rb = open_workbook('extra-words.xls', formatting_info=True)
    sheet = rb.sheet_by_index(0)
    EXTRA_WORDS = sheet.col_values(0, 0, sheet.nrows)
    return sheet.col_values(0, 0, sheet.nrows)


def get_today_extract_container_path():
    return 'extracted/%s' % datetime.today().date()


def get_today_extract_path(filename: str):
    return '%s/%s' % (get_today_extract_container_path(), filename)


def apply_emoji_filter(text: str) -> str:
    emoji_in_message = demoji.findall(text)
    for emoji in emoji_in_message.items():
        emoji_code = emoji[0]
        emoji_description = emoji[1]
        if "flag" in emoji_description:
            try:
                country = flag.dflagize(emoji_code)
                text = text.replace(emoji_code, country)
            except Exception as e:
                logging.exception(e)
                text = text.replace(emoji_code, '')
        else:
            text = text.replace(emoji_code, '')
    text = text.replace("️", "")
    return text


def extract_from_file(filepath: str) -> list:
    """
    Функция получения данных из xsl файла
    """
    result = []
    workbook = open_workbook(filepath)
    sheet = workbook.sheet_by_index(0)
    for row_index in range(sheet.nrows):
        title_cell = sheet.cell(row_index, 0)
        price_cell = sheet.cell(row_index, 1)
        result.append([title_cell.value, price_cell.value])
    return result


class Line:
    raw_text: str
    title: str
    cost: int

    def __init__(self, raw_text: str, title: str, cost: int):
        self.raw_text = raw_text
        self.title = title
        self.cost = cost

    def __str__(self):
        return self.__dict__.__str__()


def get_last_digit(text: str) -> int:
    """
    Метод поиска стоимости в строке


        Input:
                - text: str - Текст
                - filepath: str - путь к дириктории

        Output:
                - int
        Example return:
         85000
    """
    text = text.strip()
    findall_digit = []
    findall_digit = re.findall('\d+', text)
    if len(findall_digit) > 0:
        result = findall_digit[-1].strip()
        if result.isdigit() and int(result) > 999 and int(result) < 1000000:
            return result
    return None


def extract_from_text(text: str) -> list:
    """
    Метод преобразования текста в список предложений


        Input:
                - today_extract: list - Текст
                - filepath: str - путь к дириктории

        Output:
                - list(list(str, str), ...)
        Example return:
         [['apple iphone 13 256gb starlight', '83500'], ['apple iphone 15 256gb starlight', '835000']]
        Raises
        ------
            Exception
                Вывод ошибки в логи
    """
    result = []
    try:
        text = text.replace('--', '-')
        text = text.replace('*', '')
        text = text.replace('₽', '')
        text = re.sub('-+', '-', text)
        text = text.lower()
        prev_line: Line = None
        # разделить на строки
        pre_result = []
        pre_result = text.split('\n')
        # найти все строки с товарами и обработать их
        for i in pre_result:
            ci = 0
            for word in EXTRA_WORDS:
                if str.find(i, word) != -1:
                    ci = 1
                    price = get_last_digit(i)
                    # print(price)
                    if price is not None:
                        marge = i.replace(price, '')
                        result.append([marge, price])
                    else:
                        logging.info('NO PRICE ' + str(i))
            if ci == 0:
                logging.warning(i)
                # print(i)
        return (result)
    except Exception as exx:
        logging.error(exx)

    def get_text_before_dash(text: str) -> str:
        if '-' in text:
            dash_index = text.rindex('-')
            result = text[0:dash_index]
            if result:
                return result.strip()
        return None

    def join_by_one_space(t1: str, t2: str) -> str:
        return '%s %s' % (t1.strip(), t2.strip())

    for line in text.split('\n'):
        last_digit: int = get_last_digit(line)
        text_before_dash: str = None
        if last_digit:
            text_before_dash = get_text_before_dash(line)

        if prev_line:
            if text_before_dash and last_digit and not prev_line.cost:
                if prev_line.title:
                    text_before_dash = join_by_one_space(prev_line.title, text_before_dash)
                else:
                    text_before_dash = join_by_one_space(prev_line.raw_text, text_before_dash)
            elif not text_before_dash and last_digit and not prev_line.cost:
                if prev_line.title:
                    text_before_dash = prev_line.title
                elif prev_line.raw_text:
                    text_before_dash = prev_line.raw_text
            elif not prev_line.title and not prev_line.cost:
                pass
        else:
            pass

        if text_before_dash and last_digit:
            result.append([text_before_dash, last_digit])

        prev_line = Line(line, text_before_dash, last_digit)
    return result


def extract_to_xls_file(extract: list, filename: str):
    """
    Метод выгрузки текста в xls


        Input:
                - extract: list - Текст
                - filename: str - абсолютный путь


        Raises
        ------
            Exception
                Вывод ошибки в логи
    """
    workbook = Workbook()
    sheet = workbook.add_sheet("Таблица 1")
    for row_index in range(len(extract)):
        row_data = extract[row_index]
        sheet.write(row_index, 0, row_data[0])
        sheet.write(row_index, 1, row_data[1])
    try:
        makedirs(filename)
    except IOError as error:
        logging.exception(error)
    workbook.save('%s.xls' % filename)


def extract_to_today_xls_file(extract: list, filename: str):
    return extract_to_xls_file(extract, get_today_extract_path(filename))


def __fix__get_today_extract_fullpaths_by_filename(filename: str) -> list:
    result = []
    fullname = '%s.xls' % filename
    for (root, _, filenames) in walk(get_today_extract_container_path()):
        for filename0 in filenames:
            if filename0 == fullname:
                result.append(path.join(root, filename0))
    logging.info("__fix__get_today_extract_fullpaths_by_filename=[%s]" % ','.join(result))
    return result


def __dirty__delete_extract_xls_file(a: str):
    for file in __fix__get_today_extract_fullpaths_by_filename(a):
        remove(file)


def delete_extract_container_folder(a: str):
    try:
        dir_to_rm = get_today_extract_path(a)
        logging.info('delete_extract_container_folder(%s)' % dir_to_rm)
        rmtree(dir_to_rm, ignore_errors=True)
    except:
        pass


def create_today_actual_xls(filepath: str):
    xml_files = []
    today_extract_path = get_today_extract_path(filepath)

    # need to modify for support tree files
    for (root, _, filenames) in walk(today_extract_path):
        xml_files.extend(filenames)
        break

    extracts = []
    for xml_file in xml_files:
        extracts.extend(extract_from_file('%s/%s' % (today_extract_path, xml_file)))

    save_today_actual_xls(extracts, filepath)


def save_today_actual_xls(today_extract: list, filepath: str):
    """
    Метод выгрузки текста в xls


        Input:
                - today_extract: list - Текст
                - filepath: str - путь к дириктории
    """
    extract_to_xls_file(today_extract, 'public/%s/actual' % filepath)
