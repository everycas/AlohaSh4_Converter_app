from urllib.request import urlopen
import datetime as dt
import uuid
import os


class Lic:
    """ Check license params: actual date, file size etc. Returns True or False result."""

    def __init__(self):
        self.nums = (11, 12, 13, 14, 15, 16, 17, 18, 19, 110, 111, 112, 21, 22, 23, 24, 25, 26, 27, 28, 29, 210, 211,
                     212, 31, 32, 33, 34, 35, 36, 37, 38, 39, 310, 311, 312)  # номера периодов
        self.months1 = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 1)]
        self.months2 = [(1, 2, 3, 4), (2, 3, 4, 5), (3, 4, 5, 6), (4, 5, 6, 7), (5, 6, 7, 8), (6, 7, 8, 9), (7, 8, 9, 10),
                        (8, 9, 10, 11), (9, 10, 11, 12), (10, 11, 12, 1), (11, 12, 1, 2), (12, 1, 2, 3)]
        self.months3 = [(1, 2, 3, 4, 5, 6, 7), (2, 3, 4, 5, 6, 7, 8), (3, 4, 5, 6, 7, 8, 9), (4, 5, 6, 7, 8, 9, 10),
                        (5, 6, 7, 8, 9, 10, 11), (6, 7, 8, 9, 10, 11, 12), (7, 8, 9, 10, 11, 12, 1), (8, 9, 10, 11, 12, 1, 2),
                        (9, 10, 11, 12, 1, 2, 3), (10, 11, 12, 1, 2, 3, 4), (11, 12, 1, 2, 3, 4, 5), (12, 1, 2, 3, 4, 5, 6)]
        self.factor = 64  # множитель

    def check(self, log_file_name: str, res_file_name: str, ntp_url: str):

        """ Проверка файла происходит в неск.этапов:
            Первый этап проверки:
            1. Получаем размер файла.
            2. Выделяем контрольный номер периода из файла начиная с 11го символа и до символа '|'
            3. Формируем кортеж файла (контрольный номер, размер файла)
            4. Проверяем кортеж файла на наличие в списке кортежей. Если нет, возвращаем False (останавливаем проверку)
            Второй этап проверки:
            6. По контрольному номеру фиксируем рабочие месяцы
            7. Сверяем месяцы контрольного периода с месяцем сегодняшней даты. Возвращаем True/False
            8. Если check_res вернул True в итоге - то ОК, (иначе в программе удаляем файл res.dat и запрашиваем новую лицензию.) """

        check_list = [(num, (((num * self.factor) * 3) + 4) + len(str(num))) for num in self.nums]
        now = dt.datetime.now()  # Сегодняшняя дата / системное время с пк
        now_month = now.month  # сегодняшний месяц: int

        # internet datetime
        eth_dt = urlopen(ntp_url)
        eth_data = eth_dt.read().strip()
        eth_str = eth_data.decode('utf-8')  # str: 2022-04-04 09:33:46
        eth_month = int(eth_str[5:7])  # номер месяца с ntp-сервера

        # 3rd stage checking params
        uid = str(uuid.getnode())
        uid1 = uid[1:3]  # START CONTROL NUMBER
        uid2 = uid[6:8]  # END CONTROL NUMBER

        # Первый этап проверки
        if now_month == eth_month:
            try:
                file_size = os.path.getsize(res_file_name)
                with open(res_file_name) as file:
                    file_start_string = file.read(14)
                    file_end_string = file.read()
            except Exception as Argument:
                with open(log_file_name, "a") as log_file:
                    log_file.write(f"{now}: ERROR READ RES FILE: {str(Argument)}\n")
                    result = False
                    return result
            else:
                indx = file_start_string.find("|")
                if indx == -1:
                    result = False
                    return result
                else:
                    try:
                        file_num = int(file_start_string[10:indx])  # 311
                    except ValueError:
                        result = False
                        return result
                    else:
                        file_tl = (file_num, file_size)
                        if file_tl not in check_list:
                            result = False
                            return result
                        else:
                            # Второй этап проверки
                            fnum = str(file_tl[0])
                            tarif_num = int(fnum[:1])
                            period_num = int(fnum[1:])

                            working_period = []
                            if tarif_num == 1:
                                working_period.extend(list(self.months1[period_num - 1]))  # [1, 2]
                            elif tarif_num == 2:
                                working_period.extend(list(self.months2[period_num - 1]))  # [1, 2, 3, 4]
                            elif tarif_num == 3:
                                working_period.extend(list(self.months3[period_num - 1]))  # [1, 2, 3, 4, 5, 6, 7]
                            if now_month in working_period:
                                if uid1 == file_start_string[:2] and uid2 == file_end_string[-2:]:

                                    result = True  # ! CHECKING PASSED !

                                else:
                                    result = False
                                    with open("res.dat", "w") as log_file:
                                        log_file.write("00000000")

                            return result
        else:

            result = False
            return result
