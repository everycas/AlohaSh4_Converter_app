Lang: Python 3.9 Project name: NCR Aloha POS to UCS Storehouse v4 Data Converter Utility.

Aloha POS - https://www.ncr.com/restaurants/aloha-restaurant-pos-system

Storehouse 4 - https://rkeeper.com/products/r_keeper/storehouse-5-skladskoy-uchet/

Goal: Get and convert 'Aloha POS' (NCR) cash system data files:
- dictionary dbf-tables: CAT.DBF, CIT.DBF, CMP.DBF, ITM.DBF, TDR.DBF, RSN.DBF;
- shits dbf-tables: GNDITEM.DBF, GNDTNDR.DBF, GNDVOID.DBF;
to 'Storehouse v4' data files for import: Categ.dbf, Exp.dbf, Expcateg.dbf, Goods.dbf, Gtree.dbf, sunits.dbf.

Structure:
1. aloha_sh.pyw - main functionality ang gui module;
2. aloha_sh.ini - main config-file;
3. dbf_res.py - actions with aloha and sh dbf files (read, sort, filtering and write) module;
4. ini_res.py - actions with congig ini-file (read, write) module;
5. lic_res.py - licence protection module;
