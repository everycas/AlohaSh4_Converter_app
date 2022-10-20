import dbf
import pandas as pd
import datetime as dt
import shutil


class Dbf:

    def __init__(self):

        self.codepage = 'cp1251'  # кодировка
        self.now = dt.datetime.now()  # дата время пк
        self.source_path = 'SHNew'  # каталог с эталонными таблицами

    def read_dbf(self, log: str, file_path: str, file_name: str):
        """ Открыть aloha dbf файлы и вернуть pandas DataFrame. Ожидает параметры:\n
            path : путь до каталога справочников или смен без слеша на конце.\n
            file_name: 'CAT.DBF', 'CIT.DBF', 'ITM.DBF', 'RSN.DBF', 'TDR.DBF', 'CMP.DBF', 'GNDITEM.DBF', 'GNDTNDR.DBF',
            'GNDVOID.DBF'. """

        try:
            file = f"{file_path}/{file_name}"
            table = dbf.Table(file, codepage=self.codepage)

        except Exception as Argument:
            with open(log, "a") as log_file:
                log_file.write(f"{self.now}: DBF READ ERROR: {file_name}, {str(Argument)}\n")
        else:
            with table.open(dbf.READ_ONLY):
                df = pd.DataFrame(table)

                if not df.empty:
                    if file_name == 'CAT.DBF':  # категории
                        # res: [0:id, 3:name, 6:sales]
                        l = [[item[0], item[3].rstrip()] for item in df.values.tolist() if item[6] == 'Y']

                    if file_name == 'CIT.DBF':  # товары по категориям
                        # res: [0:category, 2:itemid]
                        l = [[item[0], item[2]] for item in df.values.tolist()]

                    if file_name == 'ITM.DBF':  # товары
                        # res: [0:id, 5:longname, 37:price]
                        l = [[item[0], item[5].rstrip(), item[37]] for item in df.values.tolist()]

                    if file_name == 'RSN.DBF':  # причины удалений
                        # res: [0:id, 3:name]
                        l = [[item[0], item[3].rstrip()] for item in df.values.tolist()]

                    if file_name == 'TDR.DBF':  # валюты
                        # res: [0:id, 3:name]
                        l = [[item[0], item[3].rstrip()] for item in df.values.tolist() if item[9] == 0]

                    if file_name == 'CMP.DBF':
                        # res: [0:id, 4:name, 14:rate]
                        l = [[item[0], item[4].rstrip()] for item in df.values.tolist() if item[14] == 1.0]

                    if file_name == 'GNDITEM.DBF':
                        # res: [2:check, 3:item, 5:category, 15:price, 18:dob, 23:qnt, 25:discprice]
                        l = [[item[2], item[18], item[3], item[23], item[15], item[25], item[5]] for item in
                             df.values.tolist()]  #  if item[15] >= 0

                    if file_name == 'GNDTNDR.DBF':
                        # res: [1:check, 4:type, 5:typeid]
                        l = [[item[1], item[4], item[5]] for item in df.values.tolist() if item[4] != 11]

                    if file_name == 'GNDVOID.DBF' and not df.empty:
                        # res: [2:check, 4:item, 5:price, 6:date, 10:reason]
                        l = [[item[2], item[6], item[4], item[5], item[10]] for item in df.values.tolist()]

                    result = [list(map(lambda x: x, group)) for group in l]
                    return result
                else: return []

    def write_dbf(self, log: str, tuples_list: list, file_path: str, file_name: str):
        """ Запись листов кортежей в sh dbf файл.\n
            Ожидает 'log' имя лог-файла, 'file_path' и 'file_name':\n
            'Categ.dbf', 'Exp.dbf', 'Expcateg.dbf', 'Goods.dbf', 'GTree.dbf', 'sunits.dbf' """

        table = dbf.Table(f"{file_path}/{file_name}", codepage=self.codepage)
        try:
            with table.open(dbf.READ_WRITE):
                for line in tuples_list:
                    table.append(line)
        except Exception as Argument:
            with open(log, "a") as log_file:
                log_file.write(f"{self.now}: DBF OPEN ERROR: {str(Argument)}\n")
        else:
            with open(log, "a") as log_file:
                log_file.write(str(f"{self.now}: record {file_name}... Ok. \n"))

    def new_dbf(self, log: str, path: str):
        """ Пересоздать набор sh dbf таблиц с эталонного набора.\n
            Ожидает 'log' имя лога, 'dist_path' куда перезаписывать набор таблиц. """

        file_list = ["Categ.dbf", "Exp.dbf", "Expcateg.dbf", "Goods.dbf", "GTree.dbf", "sunits.dbf"]
        try:
            for file in file_list:
                shutil.copy(f"{self.source_path}/{file}", f"{path}/{file}")  # rewrite

        except Exception as Argument:
            with open(log, "a") as log_file:
                log_file.write(f"{self.now}: DBF WRITE ERROR: {str(Argument)}\n")
        else:
            with open(log, "a") as log_file:
                log_file.write(str(f"{self.now}: create {', '.join(file_list)} ... Ok.\n"))




