from collections import Counter
import datetime as dt
from ini_res import Ini
from lic_res import Lic
from dbf_res import Dbf
import os

from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry, Calendar

# Ext modules
INI = Ini()  # модуль работы с ini-файлом
LIC = Lic()  # модуль работы с объектами лицензирования
DBF = Dbf()  # модуль работы с файлами dbf

######################################################################################
# GLOBAL VARIABLES AND CONSTANTS / Глобальные переменные и константы -----------------
######################################################################################

# GUI Colors
COLOR1 = "#D3D3D3"
COLOR2 = "#F5F5DC"
COLOR3 = "#FFBCD1"

# Names
LOG_NAME = 'aloha_sh.log'
INI_NAME = 'aloha_sh.ini'
OUT_NAME = 'SHOut'
RES_FILE_NAME = 'res.dat'

# LIC RES
NTP_URL = INI.get(log=LOG_NAME, ini=INI_NAME, section='NTP', param='url')  # строка соединения с сервером времени
LICENSE = LIC.check(log_file_name=LOG_NAME, res_file_name=RES_FILE_NAME, ntp_url=NTP_URL) # результат лицензирования

# INI PATHS
NEW_PATH = INI.get(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='new')  # путь к набору эталонных dbf-файлов SH
DICTS_PATH = INI.get(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='dicts')  # путь к базе справочников Aloha
SHIFTS_PATH = INI.get(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='shifts')  # путь к каталогу смен Aloha
RESULT_PATH = INI.get(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='result')  # путь к результирующему каталогу

# INI GROUP PARAMS
GROUPS = INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='groups')  # тип группировки документов расхода
TOTALS = INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='totals')  # суммы расхода с уч(без) скидок / наценок
TABLES = INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='tables')  # что выгружать (справочники / расход)

# ALOHA DBF DICTS Names / имена используемых при обработке таблиц справочников Aloha
TDR_NAME = 'TDR.DBF'
CMP_NAME = 'CMP.DBF'
RSN_NAME = 'RSN.DBF'
CAT_NAME = 'CAT.DBF'
CIT_NAME = 'CIT.DBF'
ITM_NAME = 'ITM.DBF'

# Aloha SHIFTS Names / имена используемых при обработке таблиц смен Aloha
GNDITEM_NAME = 'GNDITEM.DBF'
GNDTNDR_NAME = 'GNDTNDR.DBF'
GNDVOID_NAME = 'GNDVOID.DBF'

# EXPCATEG CODE RATES / добавочные коды для категорий расхода (ecateg_ref) для доп.уникализации
PAY_RATE = 10000
CUR_RATE = 20000
RSN_RATE = 30000
REFUND_RATE = 40000

# SH4 EXP / имя таблицы расхода товаров / блюд
EXP_NAME = 'exp.dbf'

# SH4 DICTS / имена таблиц справочников
EXPCATEG_NAME = 'Expcateg.dbf'
GTREE_NAME = 'GTree.dbf'
GOODS_NAME = 'Goods.dbf'
CATEG_NAME = 'Categ.dbf'
SUNITS_NAME = 'sunits.dbf'

# DATA PERIODS / используемые периоды
NOW = dt.datetime.now()
START = INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='start')
STOP = INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='stop')


###############################################################################
# MAIN DEFINITIONS / Основной функционал --------------------------------------
###############################################################################


def get_data(name: str):

    """ Получение списков кортежей данных требуемого формата для записи в целевые таблицы dbf """

    def expcateg(param: str):

        """ Категории расхода / param: 'expcateg' or 'ptree';\n
        Возвращает expcateg_tl (лист кортежей для записи в expcateg.dbf) или ptree (лист типов оплат) """

        # PAYS & PTREE (лист типов оплат)---------------------------------------------

        section = 'PTREE'
        names = INI.get(log=LOG_NAME, ini=INI_NAME, section=section, param='names').split(", ")
        codes = INI.get(log=LOG_NAME, ini=INI_NAME, section=section, param='codes').split(", ")

        ptree_l = []  # список валют из ини с привязкой к типам оплат
        pay_tl = []  # корневой уровень PTREE типы оплат

        for i in range(len(codes)):
            extcode = str(int(codes[i]) + PAY_RATE)
            name = f"pay:{names[i]}"
            deleted = '0'
            subs = INI.get(log=LOG_NAME, ini=INI_NAME, section=section, param=f"{'subs'}{codes[i]}").split(", ")

            t = (extcode, name, deleted)  # формат кортежа для записи в лист

            # pay_tl result - результирующий лист кортежей типов оплат из Алохи с учетом настроек секции ini[PTREE]
            pay_tl.append(t)  # [('20098', 'CASH', '0') ...
            ptree_l.append([extcode, name] + subs)  # ... ['20096', 'OTHERS', '24', '14', '11', '18']]

        # CURRENCIES & DISCS (лист валют и скидок) ------------------------------------------------------

        tdr = DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=TDR_NAME)

        cur_tl = []
        for l in tdr:
            extcode = str(l[0] + CUR_RATE)
            name = f"cur:{l[1]}"
            deleted = '0'

            t = (extcode, name, deleted)  # формат кортежа для записи в лист

            # cur_tl result - результирующий лист кортежей валют из Алохи с учетом настроек секции ini[PTREE]
            cur_tl.append(t)  # [('10020', 'cur:Кред.Карта', '0'), ('10001', 'cur:РУБЛИ', '0'),

        # DISCOUNTS / MARKUPS, OTHER PAYS (лист скидок, наценок и пр.оплат) ------------------------------------

        cmp = DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=CMP_NAME)

        cmp_tl = []
        for l in cmp:
            extcode = str(l[0] + CUR_RATE)
            name = f"cur:{l[1]}"
            deleted = '0'

            t = (extcode, name, deleted)  # формат кортежа для записи в лист

            # cmp_tl result - результирующий лист кортежей скидок и пр.оплат из Алохи с учетом настроек ini[PTREE]
            cmp_tl.append(t)

        # DEL REASONS (лист причин удалений / отказов) -----------------------------------------------------------

        rsn = DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=RSN_NAME)

        rsn_tl = []
        for l in rsn:
            extcode = str(l[0] + RSN_RATE)
            name = f"rsn:{l[1]}"
            deleted = '0'

            t = (extcode, name, deleted)

            # rsn_tl result - результирующий лист кортежей причин отказов из Алохи с учетом настроек секции ini[RSN]
            rsn_tl.append(t)

        # REFUND (Возврат из ini[REFUND]) -------------------------------------------------------------------------

        rfnd_code = INI.get(log=LOG_NAME, ini=INI_NAME, section='REFUND', param='code')
        rfnd_name = INI.get(log=LOG_NAME, ini=INI_NAME, section='REFUND', param='name')

        # формирование итогового листа кортежей в зависимости от параметра ini[REFUND]code /
        # если не указан то без записи "возврата"

        if len(rfnd_code) > 0 and rfnd_code.isnumeric():

            rfnd_tl = [(str(int(rfnd_code)+REFUND_RATE), f'rfnd:{rfnd_name}', '0')]
            expcateg_tl = pay_tl + cur_tl + cmp_tl + rsn_tl + rfnd_tl
        else:
            expcateg_tl = pay_tl + cur_tl + cmp_tl + rsn_tl

        # DEF RESULT (результаты выполнения функции)
        if param == 'ptree':
            return ptree_l  # (используется в других функциях)
        else:
            return expcateg_tl  # (конечный результат для записи в expcateg.dbf)

    def gtree(param: str):

        """ Дерево товаров / param: 'gtree1' or 'gtree2';\n
        Возвращает gtree_tl или gtree1 / 2 """

        ini_names = INI.get(log=LOG_NAME, ini=INI_NAME, section='GTREE', param='names').split(", ")  # list
        ini_codes = INI.get(log=LOG_NAME, ini=INI_NAME, section='GTREE', param='codes').split(", ")  # list

        # GOODS TREE (лист групп товаров / блюд ) --------------------------------------------------------------

        # 1 уровень групп товаров из ini[GTREE]
        gtree1 = []  # [[root_cat_code: num, root_cat_name: str, cat_codes], ...
        tl1 = []  # 1 уровень каталогов / категорий товаров
        for i in range(len(ini_codes)):
            extcode = int(ini_codes[i])
            parent = None
            name = ini_names[i]
            abbr = str(extcode)
            subs = INI.get(log=LOG_NAME, ini=INI_NAME, section='GTREE', param=f"{'subs'}{ini_codes[i]}").split(", ")

            t = (extcode, parent, name, abbr)  # формат кортежа для записи в лист

            # tl1 result - результирующий лист кортежей 1 уровня товаров с учетом настроек секции ini[GTREE]
            tl1.append(t)  # [(61, None, 'Алкоголь', '61'), (62, None, 'Еда', '62')]
            gtree1.append([extcode, name] + subs)  # [['61', 'Бар', '1', '3'], ...

        # 2 уровень групп товаров с привязкой к 1 уровню
        cats = DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=CAT_NAME)  # [[2, 'Бар'], [1, 'Кухня']]

        gtree2 = []
        for l1 in cats:
            ccode = str(l1[0])  # : str
            cname = str(l1[1])  # : str
            for l2 in gtree1:
                subs = l2[2:]  # срез начиная со 2-го индекса: str
                gcode = l2[0]  # int
                gname = l2[1]  # str
                if ccode in subs:
                    gtree2.append([int(ccode), cname, gcode, gname])  # [[2, 'Бар', 62, 'KUH'], ...

        # tl2 result - результирующий лист кортежей 2 уровня товаров с учетом настроек секции ini[GTREE]
        tl2 = [(x[0], x[2], x[1], str(x[0])) for x in gtree2]  # (extcode, parent, name, abbr)
        gtree_tl = tl1 + tl2  # [(61, None, 'BAR', '61'), (62, None, 'KUH', '62'), (2, 62, 'Бар', '2'), (1, 61, ...

        # DEF RESULT (результаты выполнения функции)
        if param == 'gtree1': return gtree1   # исп.в др.функциях
        elif param == 'gtree2': return gtree2  # исп.в др.функциях
        elif param == 'tl1': return tl1  # исп.в др.функциях
        else: return gtree_tl   # (конечный результат для записи в gtree.dbf)

    def goods(param: str):

        """ Товары / param option: 'goods2' """

        itm = DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=ITM_NAME)  # [[1802, 'Чизкейк', 210.0], ...
        cat = [x[0] for x in DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=CAT_NAME)]  # [[2], [1]]
        cit = [x for x in DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=CIT_NAME) if x[0] in cat]

        # ITEMS (лист товаров / блюд) --------------------------------------------------------------------------

        items = []
        for l1 in cit:
            for l2 in itm:
                if l2[0] == l1[1]:
                    items.append([l1[1], l1[0], l2[1], l2[2]])
                    # [code, parent, name, price] .. [[1802, 1, 'Чизкейк', 210.0], ...

        # goods_tl result - результирующий лист кортежей товаров / блюд
        # (extcode, parent, name, abbr_text, abbr_num, categ_ref, outtax1, outtax2, outprice, deleted, used, barcode)
        goods_tl = [(x[0], x[1], x[2], "", x[0], x[1], None, None, x[3], 0, None, "") for x in items]  # блюда
        # [(1802, 1, 'Чизкейк', '', 1802, 1, None, None, 210.0, 0, None, '') ...

        goods1 = [[x[0], x[1], x[2], x[3]] for x in items]  # [[1802, 1, 'Чизкейк', 210.0], ...
        gtree1 = gtree(param='gtree1')  # [[61, 'BAR', '1', '22'], [62, 'KUH', '2']]

        # goods2 with sunit_ref (с привязкой к категориям расхода. Исп.при формировании exp)
        goods2 = []
        for l in goods1:
            gcode = str(l[1])
            for l2 in gtree1:
                sunit = l2[0]
                if gcode in l2:
                    l.append(sunit)  #
                    goods2.append(l)  #

        # DEF RESULT (результаты выполнения функции)
        if param == 'goods2': return goods2  # (исп. в др.функциях)
        elif param == 'goods': return goods_tl  # (конечный результат для записи в gtree.dbf)
        else: return []

    def categ():

        """ Категории товаров / Create categ_tl """

        gtree2 = gtree(param='gtree2')  # [[2, 'Бар', 62, 'KUH'], ...

        # categ_tl result - результирующий лист кортежей "мест реализации товаров"
        categ_tl = [(x[0], x[1], None, 0) for x in gtree2]  # extcode, name, extoptions, deleted
        # [(2, 'Бар', None, 0), (1, 'Кухня', None, 0)]

        # DEF RESULT (результат выполнения функции)
        return categ_tl  # (конечный результат для записи в categ.dbf)

    def sunits():

        """ Места реализации / Create sunits_tl """

        tl1 = gtree(param='tl1')  # [(61, None, 'BAR', '61'), (62, None, 'KUH', '62')]
        sunits_tl = [(str(x[0]), x[2], 0) for x in tl1]  # (code, name, deleted)
        # print(sunits_tl)  # [('61', 'BAR', 0), ('62', 'KUH', 0)]

        # DEF RESULT (результат выполнения функции)
        return sunits_tl

    def shifts(start: str, stop: str, param: str):

        """ Создание листов смен из aloha shift *GND.dbf файлов.\n
         Ожидает параметры: 'gnditem', 'gndtndr', 'gndvoid'. params start/stop: 'YYYYMMDD'. """

        shifts_path = INI.get(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='shifts')

        shift_dirs = []  # лист всех каталогов смен
        for d in os.listdir(shifts_path):

            if len(d) == 8 and d.isnumeric() and d not in shift_dirs:  # проверка длины каталога и на цифровое название
                shift_dirs.append(d)  # лист каталогов: ['20211212', '20211213']

        if len(shift_dirs) != 0:  # если список отсканированных смен не пуст
            shift_dirs2 = []  # лист смен после фильтрации выбранного периода данных

            # старт/стоп в списке
            if start in shift_dirs and stop in shift_dirs:
                shift_dirs2 = shift_dirs[shift_dirs.index(start): shift_dirs.index(stop) + 1]
            # старт в списке / стоп вне списка
            elif start in shift_dirs and stop not in shift_dirs:
                shift_dirs2 = shift_dirs[shift_dirs.index(start):]
            # старт вне списка / стоп в списке
            elif start not in shift_dirs and stop in shift_dirs:
                shift_dirs2 = shift_dirs[: shift_dirs.index(stop) + 1]
            # старт/стоп директории вне списка
            elif start not in shift_dirs and stop not in shift_dirs:
                shift_dirs2 = shift_dirs  # срез старт-стоп диапазона

        items = []  # итогововый лист расхода товаров
        tndrs = []  # итоговый лист расхода товаров по оплатам
        voids = []  # итоговый лист расхода товаров по причинам отказов

        for shift_dir in shift_dirs2:  # добавление смен из выбранного периода в общие списки
            items.extend(DBF.read_dbf(log=LOG_NAME, file_path=f"{SHIFTS_PATH}/{shift_dir}", file_name=f"{GNDITEM_NAME}"))
            tndrs.extend(DBF.read_dbf(log=LOG_NAME, file_path=f"{SHIFTS_PATH}/{shift_dir}", file_name=f"{GNDTNDR_NAME}"))
            voids.extend(DBF.read_dbf(log=LOG_NAME, file_path=f"{SHIFTS_PATH}/{shift_dir}", file_name=f"{GNDVOID_NAME}"))

        # DEF RESULT (результаты выполнения функции)
        if param == GNDITEM_NAME: return items
        elif param == GNDTNDR_NAME: return tndrs
        elif param == GNDVOID_NAME: return voids
        else: return []

    def exp():

        """ Расход товаров / params: '1' - by cur's, '2' - by pay types, '3' - by del reasons """

        START = INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='start')
        STOP = INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='stop')

        GROUPS = INI.get(ini=INI_NAME, log=LOG_NAME, section='EXP', param='groups')
        TOTALS = INI.get(ini=INI_NAME, log=LOG_NAME, section='EXP', param='totals')

        items = shifts(start=START, stop=STOP, param=GNDITEM_NAME)
        # [[20001, datetime.date(2022, 4, 5), 2900, 1.0, 380.0, 380.0, 1], .. categ]
        tndrs = shifts(start=START, stop=STOP, param=GNDTNDR_NAME)  # [[20001, 1, 20], ... check, pay_id, cur

        goods2 = goods('goods2')  # [[1802, 1, 'Чизкейк', 210.0, 61], ...
        ptree = expcateg('ptree')  # ... ['10096', 'pay:OTHERS', '24', '14', '11', '18']]

        # GND ITEMS FULL LIST (расширенный список расхода товаров) --------------------------------------------------
        items2 = []
        for l in items:
            check = l[0]
            item = l[2]
            for l2 in tndrs:
                check2 = l2[0]
                cur = l2[2]
                if check == check2 and len(l) < 8:
                    l.append(cur)  # [20001, datetime.date(2022, 4, 5), 2900, 1.0, 380.0, 380.0, 1, 20]
                    # [check, date, item, quantity, price, discprice, categ, cur]
            for l3 in goods2:
                item2 = l3[0]
                sunit = l3[4]
                name = l3[2]
                if item == item2:
                    l.append(sunit)  # ... , 220.0, 10001, 62]  # ... cur, sunit]
                    l.append(name)  # ... curr, sunit, item_name]
                    # [20001, datetime.date(2022, 4, 5), 2900, 1.0, 380.0, 380.0, 1, 20, 61, 'Ролл с лососем 200 гр']
            for l4 in ptree:  # ... ['10096', 'pay:OTHERS', '24', '14', '11', '18']]
                pay = int(l4[0])  # 10096
                curs = l4[2:]  # ['24', '14', '11', '18'] ..
                if str(l[7]) in curs:
                    l.append(pay)
                    items2.append(l)

        # items2 result:
        # [[20001, datetime.date(2022, 4, 5), 2900, 1.0, 380.0, 380.0, 1, 20, 61, 'Ролл с лососем 200 гр', 10099],
        # [check, date, item, quantity, price, discprice, categ, cur, sunit, name, pay_type]

        # EXP ITEMS TL (расход товаров / блюд) ----------------------------------------------------------------

        tl0 = []
        for l in items2:
            logicdate = l[1]
            sunits_ref = str(l[8])
            goods_ref = l[2]
            pgoods_ref = None
            # в завис. от того, какой тип группировки документов расхода выбран в gui / ini[EXP]groups
            if GROUPS == '2': ecateg_ref = l[7] + CUR_RATE  # by currs / по валютам
            elif GROUPS == '1': ecateg_ref = l[-1]  # by pay types / по типам оплат
            elif GROUPS == '3': ecateg_ref = None  # by del reasons / по причинам отказов / удалений блюд
            else: ecateg_ref = None

            ecaption_ref = None
            qnt = l[3]
            if TOTALS == '1': total = l[5]  # with discs / markups
            if TOTALS == '2': total = l[6]  # without

            gabbr_text = ""
            gabbr_num = str(l[2])
            gname = l[9]

            t = (logicdate, sunits_ref, goods_ref, pgoods_ref, ecateg_ref, ecaption_ref, qnt, total,
                 gabbr_text, gabbr_num, gname)
            tl0.append(t)

            # result:
            # [(datetime.date(2022, 4, 5), '61', 2900, None, 20020, None, 1.0, 380.0, '', '2900', 'Ролл с лососем 200

        # REFUNDS (добавление в exp данных по возвратам) ----------------------------------------------------------

        rfnd_ini_code = INI.get(log=LOG_NAME, ini=INI_NAME, section='REFUND', param='code')

        if len(rfnd_ini_code) > 0 and rfnd_ini_code.isnumeric():
            for t in tl0:
                total0 = t[7]
                if total0 < 0:
                    to_ins = (t[0], t[1], t[2], t[3], int(rfnd_ini_code)+REFUND_RATE, t[5], t[6], abs(t[7]), t[8], t[9], t[10])
                    for_del = (t[0], t[1], t[2], t[3], t[4], t[5], t[6], abs(t[7]), t[8], t[9], t[10])
                    tl0.remove(t)
                    tl0.remove(for_del)
                    tl0.append(to_ins)

        elif len(rfnd_ini_code) == 0 or not rfnd_ini_code.isnumeric():
            for t in tl0:
                total0 = t[7]
                if total0 < 0:
                    for_del = (t[0], t[1], t[2], t[3], t[4], t[5], t[6], abs(t[7]), t[8], t[9], t[10])
                    tl0.remove(t)
                    tl0.remove(for_del)
                    # [(datetime.date(2022, 4, 5), '62', 1803, None, 20001, None, 1.0, -100.0, '', '1803', 'Круассан')]

        # result / лист кортежей расхода товаров / блюд с возвратами
        tl1 = tl0

        # VOIDS TL (добавление листа кортежей расхода блюд по отказам / причинам удалений) --------------------------

        voids = shifts(start=START, stop=STOP, param=GNDVOID_NAME)
        # [[20604, datetime.date(2022, 4, 5), 1806, 130.0, 5], ... reason]

        # Передается в TL, если код причины удаления есть в [RSN]reasons
        voids2 = []
        for l in voids:
            code = l[2]
            for l2 in goods2:  # [[1802, 1, 'Чизкейк', 210.0, 61], ...
                code2 = l2[0]
                name = l2[2]
                sunit = l2[4]
                if code == code2:
                    l.append(name)  # ... , 'Хот-Дог']
                    l.append(sunit)  # ... -Дог', 61]
                    voids2.append(l)  # [[20604, datetime.date(2022, 4, 5), 1806, 130.0, 5, 'Круассан с шоколадом', 61],
        ini_reasons = INI.get(log=LOG_NAME, ini=INI_NAME, section='RSN', param='reasons').split(", ")
        del_reasons = [int(x) for x in ini_reasons]

        tl2 = []
        for l in voids2:  # [[20604, datetime.date(2022, 4, 5), 1806, 130.0, 5, 'Круассан с шоколадом', 61],
            if l[4] in del_reasons:
                logicdate = l[1]
                sunits_ref = str(l[6])
                goods_ref = l[2]
                pgoods_ref = None
                ecateg_ref = l[4] + RSN_RATE
                ecaption_ref = None
                qnt = 1.0
                total = l[3]
                gabbr_text = ""
                gabbr_num = str(l[2])
                gname = l[5]
                t = (logicdate, sunits_ref, goods_ref, pgoods_ref, ecateg_ref, ecaption_ref, qnt, total,
                     gabbr_text, gabbr_num, gname)
                tl2.append(t)  #

        # result / результирующий лист кортежей расхода блюд с учетом данных о возвратах, отказах, удалениях
        tl = tl1 + tl2

        # Получение конечного RES_TL (ITEMS + REFUNDS + VOIDS) просуммированного по кол-ву

        c = Counter(tl)
        exp_dict = c

        logicdate_l = []
        sunits_ref_l = []  # str,2
        goods_ref_l = []
        pgoods_ref_l = []
        ecateg_ref_l = []  # int,15
        ecaption_ref_l = []
        qnt_l = []
        total_l = []
        gabbr_text_l = []
        gabbr_num_l = []
        gname_l = []  # str,47

        for k in exp_dict:
            # print(k[2], exp_dict[k])
            logicdate_l.append(k[0])
            sunits_ref_l.append(k[1])
            goods_ref_l.append(k[2])
            pgoods_ref_l.append(k[3])
            ecateg_ref_l.append(k[4])
            ecaption_ref_l.append(k[5])
            qnt_l.append(float(exp_dict[k]))
            total_l.append(k[7] * exp_dict[k])
            gabbr_text_l.append(k[8])
            gabbr_num_l.append(k[9])
            gname_l.append(k[10])

        res_tl = list(zip(logicdate_l, sunits_ref_l, goods_ref_l, pgoods_ref_l, ecateg_ref_l, ecaption_ref_l, qnt_l,
                      total_l, gabbr_text_l, gabbr_num_l, gname_l))

        # DEF RESULT (результаты выполнения функции)
        return res_tl

    # ALL GET DATA DEF ACTIONS / Запрос получаемых листов и листов кортежей
    if name == 'expcateg': return expcateg(param='expcateg')
    elif name == 'ptree': return expcateg(param='ptree')
    elif name == 'tl1': return gtree(param='tl1')
    elif name == 'gtree': return gtree(param='gtree')
    elif name == 'gtree1': return gtree(param='gtree1')
    elif name == 'gtree2': return gtree(param='gtree2')
    elif name == 'goods': return goods(param='goods')
    elif name == 'goods2': return goods(param='goods2')
    elif name == 'categ': return categ()
    elif name == 'sunits': return sunits()
    elif name == 'exp': return exp()
    else: []


def import_rk():

    """ Запуск модуля ImportRK из состава SH4, если настроены параметры в ini[AUTO] """

    import subprocess

    null_date = dt.datetime(year=1900, month=1, day=1)
    path = INI.get(log=LOG_NAME, ini=INI_NAME, section='AUTO', param='import')
    sdb = INI.get(log=LOG_NAME, ini=INI_NAME, section='AUTO', param='sdb')

    rcode = '1'
    flag = '0'

    START = INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='start')
    start_date = dt.datetime(year=int(START[:4]), month=int(START[4:6]), day=int(START[6:8]))

    start_l = str(start_date - null_date).split(" ")
    start = start_l[0]

    if path != "" and sdb != "" and start != "":
        importrk_string = f"{path} {sdb} {rcode} {start} {flag}"
        subprocess.Popen(importrk_string)
    elif path != "":
        importrk_string = f"{path}"
        subprocess.Popen(importrk_string)
    else:
        with open(LOG_NAME, "a") as log_file:
            log_file.write(str(f"{NOW}: INI ERROR : [AUTO] params.\n"))


def gui():

    """ Интерфейс программы / GUI """

    ####################################################################################
    # MENU FILE / Вкладка функционального меню "Файл" ----------------------------------
    ####################################################################################

    def gui_menu_file_start():
        """ Функциональная вкладка 'Start'  """
        # in group params
        tables = INI.get(ini=INI_NAME, log=LOG_NAME, section='EXP', param='tables')

        # Dicts (получение листов кортежей таблиц справочников)
        categ_tl = get_data('categ')
        expcateg_tl = get_data('expcateg')
        gtree_tl = get_data('gtree')
        goods_tl = get_data('goods')
        sunits_tl = get_data('sunits')

        # Expenditure (получение расхода блюд / товаров)
        exp_tl = get_data('exp')

        names = ['Categ.dbf', 'Expcateg.dbf', 'GTree.dbf', 'Goods.dbf', 'sunits.dbf', 'Exp.dbf']
        tables_l = [categ_tl, expcateg_tl, gtree_tl, goods_tl, sunits_tl, exp_tl]

        # write new tables / перезапись итоговых файлов dbf на новые (чистые)
        DBF.new_dbf(log=LOG_NAME, path=RESULT_PATH)

        # dbf record / запись данных (и занесение результатов в лог-файл) листов кортежей в целевые таблицы dbf
        if tables == '1':  # Dicts + Exp / ini[EXP]tables
            for i in range(len(names)):
                with open(LOG_NAME, "a") as log_file:
                    log_file.write(f"{NOW} : Start creating {names[i]} ...\n")
                DBF.write_dbf(log=LOG_NAME, file_path=RESULT_PATH, file_name=names[i], tuples_list=tables_l[i])
                with open(LOG_NAME, "a") as log_file:
                    log_file.write(f"{NOW} : {names[i]} Ok!\n")

        if tables == '2':  # Dicts only (запись только справочников)
            for i in range(len(names[:5])):
                with open("aloha_sh.log", "a") as log_file:
                    log_file.write(f"{NOW} : Start creating {names[i]} ...\n")
                DBF.write_dbf(log=LOG_NAME, file_path=RESULT_PATH, file_name=names[i], tuples_list=tables_l[i])
                with open("aloha_sh.log", "a") as log_file:
                    log_file.write(f"{NOW} : {names[i]} Ok!\n")

        if tables == '3':  # Exp only (только расход)
            with open("aloha_sh.log", "a") as log_file:
                log_file.write(f"{NOW} : Start creating {names[-1]} ...\n")
            DBF.write_dbf(log=LOG_NAME, file_path=RESULT_PATH, file_name=names[-1], tuples_list=tables_l[-1])
        # Done! message
        messagebox.showinfo(title='Convert', message='Done!')

        # Start ImportRK / Запуск модуля импорта из состава Sh4
        import_rk()
        # Завершение работы программы
        root.destroy()

    ####################################################################################
    # MENU SETTINGS / Вкладка функционального меню Настройки ---------------------------
    ####################################################################################

    def gui_menu_settings_paths():

        """ Функционал вкладки функционального меню настройки путей """

        def button_save_paths():

            """ Функция кнопки сохранение путей """

            # menu settings entries enabled
            settings.entryconfigure(0, state='normal')
            settings.entryconfigure(2, state='normal')
            settings.entryconfigure(4, state='normal')
            # write paths from entries to ini
            INI.set(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='dicts', data=entry_dicts.get())
            INI.set(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='shifts', data=entry_shifts.get())
            INI.set(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='result', data=entry_result.get())
            # destroy
            button_save.destroy()
            entry_dicts.destroy()
            entry_shifts.destroy()
            entry_result.destroy()
            label_paths.destroy()
            root.maxsize(width=245, height=250)

        ########################################################################################
        # GUI MENU SETTINGS PATHS / Интерфейс окна функционального меню настройки путей --------
        ########################################################################################

        # menu settings entries disabled
        settings.entryconfigure(0, state='disabled')
        settings.entryconfigure(2, state='disabled')
        settings.entryconfigure(4, state='disabled')
        # root window extend
        root.maxsize(width=245, height=400)
        # Paths
        label_paths = Label(text="Paths: dicts, shifts, result", width=22)
        label_paths.grid(column=0, row=7, sticky=NW)
        # Путь к справочникам
        entry_dicts = Entry(width=28, relief="sunken", bg=COLOR2)
        entry_dicts.insert(0, INI.get(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='dicts'))
        entry_dicts.grid(column=0, row=8, padx=3, pady=5, sticky=NW)
        # Путь к сменам
        entry_shifts = Entry(width=28, relief="sunken", bg=COLOR2)
        entry_shifts.insert(0, INI.get(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='shifts'))
        entry_shifts.grid(column=0, row=9, padx=3, pady=5, sticky=NW)
        # Путь к выгрузке
        entry_result = Entry(width=28, relief="sunken", bg=COLOR2)
        entry_result.insert(0, INI.get(log=LOG_NAME, ini=INI_NAME, section='PATHS', param='result'))
        entry_result.grid(column=0, row=10, padx=3, pady=5, sticky=NW)
        # Save
        button_save = Button(text="Save", width=5, height=1, bg=COLOR3, command=button_save_paths)
        button_save.grid(column=0, row=11, padx=3, pady=5, sticky=SE)

    def gui_menu_settings_links():

        """ Функционал вкладки функционального меню отображения привязок категорий GTREE,
         PTREE, RSN """

        def unlinked_gtree_codes():

            """ Список (не)привязанных категорий ini[GTREE] """

            cat = DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=CAT_NAME)  # [[2, 'Бар'], [1, 'Кухня']]
            linked_codes = [x[0] for x in get_data('gtree2')]  # [2]
            unlinked = [f' {x[0]}: {x[1]}->UNLINKED!' for x in cat if x[0] not in linked_codes]
            unlinked.sort()
            linked = [f' {x[0]}: {x[1]}->{x[2]}: {x[3]}' for x in get_data('gtree2')]
            linked.sort()
            result = unlinked + linked
            return result

        def unlinked_ptree_codes():

            """ Список (не)привязанных категорий ini[PTREE] """

            tdr = DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=TDR_NAME)  # [[20, 'Кред.Карта'], ...
            linked_codes = [x[2:] for x in get_data('ptree') if x[2] != '']
            linked_codes2 = [item for sublist in linked_codes for item in sublist]
            unlinked = [f" {x[0]}: {x[1]}->UNLINKED!" for x in tdr if str(x[0]) not in linked_codes2]
            linked = []
            for x in tdr:
                code = str(x[0])
                name = x[1]
                for y in get_data('ptree'):
                    code_l = y[2:]
                    if code in code_l:
                        l = f" {code}: {name}->{int(y[0]) - PAY_RATE}: {y[1].lstrip('pay:')}"
                        linked.append(l)
            unlinked.sort()
            linked.sort()

            return unlinked + linked

        def unlinked_rsn_codes():

            """ Список (не)привязанных категорий ini[RSN] """

            rsn = DBF.read_dbf(log=LOG_NAME, file_path=DICTS_PATH, file_name=RSN_NAME)  # [[1, 'Ошибка официант'], ..
            linked_codes = INI.get(log=LOG_NAME, ini=INI_NAME, section='RSN', param='reasons').split(', ')
            linked = [f'{x[0]}: {x[1]}->linked OK!' for x in rsn if str(x[0]) in linked_codes]
            unlinked = [f'{x[0]}: {x[1]}->UNLINKED!' for x in rsn if str(x[0]) not in linked_codes]
            linked.sort()
            unlinked.sort()

            return unlinked + linked

        def button_close_links():

            """ Функционал кнопки Close в окне просмотра привязки категорий """

            # menu settings entries enabled
            settings.entryconfigure(0, state='normal')
            settings.entryconfigure(2, state='normal')
            settings.entryconfigure(4, state='normal')
            # destroy
            gtree_label.destroy()
            gtree_listbox.destroy()
            ptree_label.destroy()
            ptree_listbox.destroy()
            rsn_label.destroy()
            rsn_listbox.destroy()
            button_close.destroy()
            button_update.destroy()
            # resize back main window
            root.maxsize(width=245, height=250)

        def button_update_lists():

            """ Функционал кнопки Update lists в окне просмотра привязки категорий"""

            # clear listboxes
            gtree_listbox.delete(0, END)
            ptree_listbox.delete(0, END)
            rsn_listbox.delete(0, END)

            # fill gtree listbox
            unlinked_gtree = unlinked_gtree_codes()
            if len(unlinked_gtree) > 0:
                for item in unlinked_gtree:
                    gtree_listbox.insert(unlinked_gtree.index(item), item)

            # fill ptree listbox
            unlinked_ptree = unlinked_ptree_codes()
            for item in unlinked_ptree:
                ptree_listbox.insert(unlinked_ptree.index(item), item)

            # fill rsn listbox
            unlinked_rsn = unlinked_rsn_codes()
            for item in unlinked_rsn:
                rsn_listbox.insert(unlinked_rsn.index(item), item)

        #######################################################################################################
        # GUI LINKS / Интерфейс окна привязок категорий GTREE, PTREE, RSN -------------------------------------
        #######################################################################################################

        # menu settings entries disabled
        settings.entryconfigure(0, state='disabled')
        settings.entryconfigure(2, state='disabled')
        settings.entryconfigure(4, state='disabled')
        # root window extend
        root.maxsize(width=480, height=490)

        # GTREE -----------------------------------------------------------
        # Unlinked Categ's Label
        gtree_label = Label(text="Unlinked [GTREE] codes", width=21)
        gtree_label.grid(column=0, row=7, padx=3, sticky=NW)

        # Unlinked Categ's Listbox
        gtree_listbox = Listbox(height=10, width=28, exportselection="false", bg=COLOR2)
        unlinked_gtree = unlinked_gtree_codes()
        if len(unlinked_gtree) > 0:
            for item in unlinked_gtree:
                gtree_listbox.insert(unlinked_gtree.index(item), item)
        gtree_listbox.bind("<<ListboxSelect>>", None)
        gtree_listbox.grid(column=0, row=8, padx=3, pady=3, sticky=NW, rowspan=2)

        # PTREE -------------------------------------------------------------
        # Unlinked Currs's Label
        ptree_label = Label(text="Unlinked [PTREE] codes", width=21)
        ptree_label.grid(column=1, row=0, padx=3, sticky=NW)
        # Unlinked curr's Listbox
        ptree_listbox = Listbox(height=9, width=28, exportselection="false", bg=COLOR2)
        unlinked_ptree = unlinked_ptree_codes()
        for item in unlinked_ptree:
            ptree_listbox.insert(unlinked_ptree.index(item), item)
        ptree_listbox.bind("<<ListboxSelect>>", None)
        ptree_listbox.grid(column=1, row=1, padx=3, pady=3, sticky=NW, rowspan=6)

        # RSN -------------------------------------------------------------
        # Unlinked RSN's Label
        rsn_label = Label(text="Unlinked [RSN] codes", width=20)
        rsn_label.grid(column=1, row=7, padx=3, sticky=NW)
        # Unlinked RSN's Listbox
        rsn_listbox = Listbox(height=8, width=28, exportselection="false", bg=COLOR2)
        unlinked_rsn = unlinked_rsn_codes()
        for item in unlinked_rsn:
            rsn_listbox.insert(unlinked_rsn.index(item), item)
        rsn_listbox.bind("<<ListboxSelect>>", None)
        rsn_listbox.grid(column=1, row=8, padx=3, pady=3, sticky=NW)
        # Save button
        button_close = Button(text="Close", width=6, height=1, bg=COLOR3, command=button_close_links)
        button_close.grid(column=1, row=9, padx=3, pady=5, sticky=SE)
        # update button
        button_update = Button(text='Update lists \u27F3', width=13, height=1, bg=COLOR3, command=button_update_lists)
        button_update.grid(column=1, row=9, padx=3, pady=5, sticky=SW)

    def gui_menu_settings_impRK():

        """ Функционал вкладки функционального меню настроек модуля ImportRK """

        def button_save_imprk():

            """ Функционал кнопки Save окна настроек модуля ImportRK  """

            # menu settings entries enabled
            settings.entryconfigure(0, state='normal')
            settings.entryconfigure(2, state='normal')
            settings.entryconfigure(4, state='normal')
            # write paths from entries to ini
            INI.set(log=LOG_NAME, ini=INI_NAME, section='AUTO', param='import', data=entry_imprk.get())
            INI.set(log=LOG_NAME, ini=INI_NAME, section='AUTO', param='sdb', data=entry_sdb.get())
            # destroy
            label_imprk.destroy()
            entry_imprk.destroy()
            label_sdb.destroy()
            entry_sdb.destroy()
            button_imprk.destroy()
            # resize back main window
            root.maxsize(width=245, height=250)

        #################################################################################################
        # GUI MENU SETTINGS ImpRK / Интерфейс окна настроек модуля ImportRK -----------------------------
        #################################################################################################

        # menu settings entries disabled
        settings.entryconfigure(0, state='disabled')
        settings.entryconfigure(2, state='disabled')
        settings.entryconfigure(4, state='disabled')
        # root window extend
        # root.minsize(width=245, height=400)
        root.maxsize(width=245, height=400)
        # ImpRK path label
        label_imprk = Label(text="ImportRK.exe path", width=18)
        label_imprk.grid(column=0, row=7, sticky=NW)
        # imprk entry
        entry_imprk = Entry(width=28, relief="sunken", bg=COLOR2)
        entry_imprk.insert(0, INI.get(log=LOG_NAME, ini=INI_NAME, section='AUTO', param='import'))
        entry_imprk.grid(column=0, row=8, padx=3, pady=5, sticky=NW)
        # sdb label
        label_sdb = Label(text="Sdb_reg connection string", width=23)
        label_sdb.grid(column=0, row=9, sticky=NW)
        # sdb entry
        entry_sdb = Entry(width=28, relief="sunken", bg=COLOR2)
        entry_sdb.insert(0, INI.get(log=LOG_NAME, ini=INI_NAME, section='AUTO', param='sdb'))
        entry_sdb.grid(column=0, row=10, padx=3, pady=5, sticky=NW)

        # ImpRK Save
        button_imprk = Button(text="Save", width=5, height=1, bg=COLOR3, command=button_save_imprk)
        button_imprk.grid(column=0, row=11, padx=3, pady=5, sticky=SE)

    #############################################################################################
    # MENU HELP / Вкладка функционального меню Помощь -------------------------------------------
    #############################################################################################

    def menu_hlp_about():
        messagebox.showinfo(title="About", message="Aloha POS to SH4 Data Converter. Shareware. Version 3.5 release\n"
                                                   "Created by Dmitry R. Support: everycas@gmail.com.\n\n"
                                                   "Installation and user manual please see in docs folder.")

    def menu_hlp_license():
        messagebox.showinfo(title='License', message=f"Valid license: {LICENSE}.")

    ##########################################################################################
    # MAIN / Функции селекторов основного окна -----------------------------------------------
    ##########################################################################################

    def pick_start(event):
        date = str(picker_start.get_date())
        start_date = ''.join(date.split('-'))  # str : 20220401
        INI.set(log=LOG_NAME, ini=INI_NAME, section='EXP', param='start', data=start_date)

    def pick_stop(event):
        date = str(picker_stop.get_date())
        stop_date = ''.join(date.split('-'))  # str : 20220401
        INI.set(log=LOG_NAME, ini=INI_NAME, section='EXP', param='stop', data=stop_date)

    def cbox_groups_set(event):
        num = str(int(cbox_groups['values'].index(cbox_groups.get())) + 1)
        INI.set(log=LOG_NAME, ini=INI_NAME, section='EXP', param='groups', data=num)

    def cbox_totals_set(event):
        num = str(int(cbox_totals['values'].index(cbox_totals.get())) + 1)
        INI.set(log=LOG_NAME, ini=INI_NAME, section='EXP', param='totals', data=num)

    def cbox_tables_set(event):
        num = str(int(cbox_tables['values'].index(cbox_tables.get())) + 1)
        INI.set(log=LOG_NAME, ini=INI_NAME, section='EXP', param='tables', data=num)

    ######################################################################################
    # GUI MAIN WINDOW / Основное окно программы ------------------------------------------
    ######################################################################################

    root = Tk()
    root.iconbitmap('logo.ico')
    root.title("AlohaSH")
    root.config(padx=5, pady=5)
    root.maxsize(width=245, height=250)
    root.resizable(False, False)

    ####################################################################################
    # FILE MENU / Функциональное меню / Вкладки ----------------------------------------
    ####################################################################################

    main = Menu(root)
    root.config(menu=main)
    # File
    file = Menu(main, tearoff=0)
    file.add_command(label="Start", command=gui_menu_file_start)
    file.add_separator()
    file.add_command(label="Exit", command=root.destroy)
    # Settings
    settings = Menu(main, tearoff=0)
    settings.add_command(label="Set data paths", command=gui_menu_settings_paths)
    settings.add_separator()
    settings.add_command(label="Show unlinked codes", command=gui_menu_settings_links)
    settings.add_separator()
    settings.add_command(label="Set auto_import", command=gui_menu_settings_impRK)
    # Help
    hlp = Menu(main, tearoff=0)
    hlp.add_command(label="About", command=menu_hlp_about)
    hlp.add_command(label="License", command=menu_hlp_license)
    # Root menu level
    main.add_cascade(label="File", menu=file)
    main.add_cascade(label="Settings", menu=settings)
    main.add_cascade(label="Help", menu=hlp)

    #######################################################
    # DATE / CALENDAR PICKERS / Календари -----------------
    #######################################################

    # Label start
    date_label = Label(text="Start - stop data period", width=20)
    date_label.grid(column=0, row=0, padx=3, sticky=NW)
    # Start picker
    picker_start = DateEntry(selectmode='day', year=NOW.year, month=NOW.month, day=NOW.day - 1, locale='ENG')
    picker_start.config(width=25)
    picker_start.bind("<<DateEntrySelected>>", pick_start)
    picker_start.grid(column=0, row=1, pady=3, padx=3, sticky=NW)
    # Stop picker
    picker_stop = DateEntry(selectmode='day', year=NOW.year, month=NOW.month, day=NOW.day, locale='ENG')
    picker_stop.config(width=25)
    picker_stop.bind("<<DateEntrySelected>>", pick_stop)
    picker_stop.grid(column=0, row=2, pady=3, padx=3, sticky=NW)

    ###################################################################
    # COMBO_BOXES / Выбор группировок ---------------------------------
    ###################################################################

    label_group = Label(text="Group EXP doc's", width=13)
    label_group.grid(column=0, row=3, padx=3, sticky=NW)
    # 1
    n = StringVar()
    cbox_groups = ttk.Combobox(root, width=25, textvariable=n, state="readonly")
    cbox_groups['values'] = ('1) By pay types', '2) By currencies', '3) By del reasons')
    cbox_groups.bind("<<ComboboxSelected>>", cbox_groups_set)
    cbox_groups.grid(column=0, row=4, pady=3, padx=3, sticky=NW)
    cbox_groups.current(int(INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='groups')) - 1)
    # 2
    n2 = StringVar()
    cbox_totals = ttk.Combobox(root, width=25, textvariable=n2, state="readonly")
    cbox_totals['values'] = ("1) With disc's / markups", "2) Without disc's / markups")
    cbox_totals.bind("<<ComboboxSelected>>", cbox_totals_set)
    cbox_totals.grid(column=0, row=5, pady=3, padx=3, sticky=NW)
    cbox_totals.current(int(INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='totals')) - 1)
    # 3
    n3 = StringVar()
    cbox_tables = ttk.Combobox(root, width=25, textvariable=n3, state="readonly")
    cbox_tables['values'] = ("1) Dict's + Exp's", "2) Dict's only", "3) Exp's only")
    cbox_tables.bind("<<ComboboxSelected>>", cbox_tables_set)
    cbox_tables.grid(column=0, row=6, pady=3, padx=3, sticky=NW)
    cbox_tables.current(int(INI.get(log=LOG_NAME, ini=INI_NAME, section='EXP', param='tables')) - 1)

    # Основная рабочая петля отображения интерфейса
    root.mainloop()


def auto():

    """ Автоматический (консольный) режим работы при ini[GUI]mode = 0 """

    global START, STOP
    # date
    today = str(NOW.date())
    # чистка от символов
    date = int(today.replace("-", ''))  # : int 20220421
    start_date = str(date - 1)
    # запись старт-стоп даты в ини
    START = INI.set(log=LOG_NAME, ini=INI_NAME, section='EXP', param='start', data=start_date)
    STOP = INI.set(log=LOG_NAME, ini=INI_NAME, section='EXP', param='stop', data=str(date))

    # in group params
    tables = INI.get(ini=INI_NAME, log=LOG_NAME, section='EXP', param='tables')
    # Dicts
    categ_tl = get_data('categ')
    expcateg_tl = get_data('expcateg')
    gtree_tl = get_data('gtree')
    goods_tl = get_data('goods')
    sunits_tl = get_data('sunits')
    # Expenditure
    exp_tl = get_data('exp')

    names = ['Categ.dbf', 'Expcateg.dbf', 'GTree.dbf', 'Goods.dbf', 'sunits.dbf', 'Exp.dbf']
    tables_l = [categ_tl, expcateg_tl, gtree_tl, goods_tl, sunits_tl, exp_tl]

    # write new tables
    DBF.new_dbf(log=LOG_NAME, path=RESULT_PATH)
    # dbf record
    if tables == '1':  # Dicts + Exp
        for i in range(len(names)):
            with open(LOG_NAME, "a") as log_file:
                log_file.write(f"{NOW} : Start creating {names[i]} ...\n")
            DBF.write_dbf(log=LOG_NAME, file_path=RESULT_PATH, file_name=names[i], tuples_list=tables_l[i])
            with open(LOG_NAME, "a") as log_file:
                log_file.write(f"{NOW} : {names[i]} Ok!\n")

    if tables == '2':  # Dicts only
        for i in range(len(names[:5])):
            with open(LOG_NAME, "a") as log_file:
                log_file.write(f"{NOW} : Start creating {names[i]} ...\n")
            DBF.write_dbf(log=LOG_NAME, file_path=RESULT_PATH, file_name=names[i], tuples_list=tables_l[i])
            with open(LOG_NAME, "a") as log_file:
                log_file.write(f"{NOW} : {names[i]} Ok!\n")

    else:  # Exp only
        with open(LOG_NAME, "a") as log_file:
            log_file.write(f"{NOW} : Start creating {names[-1]} ...\n")
        DBF.write_dbf(log=LOG_NAME, file_path=RESULT_PATH, file_name=names[-1], tuples_list=tables_l[-1])
    # Done! message
    with open(LOG_NAME, "a") as log_file:
        log_file.write(f"{NOW} : Exit.\n")

    # Start ImportRK
    import_rk()


def run():

    """ Старт (запуск) программы """

    with open("aloha_sh.log", "w") as log_file:
        log_file.write(f"{NOW} : Start.\n")

    # GUI
    if LICENSE:  # Если модуль проверки лицензии вернул True
        if INI.get(log=LOG_NAME, ini=INI_NAME, section='GUI', param='mode') == '1':
            gui()
        else:
            auto()
    else:
        messagebox.showerror(title="License error", message=f'Valid license: {LICENSE}.\n\n'
                                                            'For new license and support contact to:\n'
                                                            'everycas@gmail.com')


run()

