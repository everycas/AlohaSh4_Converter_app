Lang: Python 3.9 Project name: NCR Aloha POS to UCS Storehouse v4 Data Converter Utility.

Aloha POS - https://www.ncr.com/restaurants/aloha-restaurant-pos-system

Storehouse 4 - https://rkeeper.com/products/r_keeper/storehouse-5-skladskoy-uchet/

Goal: Get and convert 'Aloha POS' (NCR) cash system data files:
- dictionary dbf-tables: CAT.DBF, CIT.DBF, CMP.DBF, ITM.DBF, TDR.DBF, RSN.DBF;
- shits dbf-tables: GNDITEM.DBF, GNDTNDR.DBF, GNDVOID.DBF;

to 'Storehouse v4' data files for import: 
- Categ.dbf, Exp.dbf, Expcateg.dbf, Goods.dbf, Gtree.dbf, sunits.dbf.

Project structure:
1. aloha_sh.pyw - main functionality ang gui module;
2. aloha_sh.ini - main config-file;
3. dbf_res.py - actions with aloha and sh dbf files (read, sort, filtering and write) module;
4. ini_res.py - actions with congig ini-file (read, write) module;
5. lic_res.py - licence protection module;
6. \SHNew - etalon SH import dbf-tables
7. \SHOut - result tables after convert actions
8. \SHImp - SHImport utility (import converted result dbf-tables to SH4 Base)
9. \AlohaTS\DATA - AlohaPOS Database (Dicts) sample
10. \AlohaTS\YYYYMMDD - AlohaPOS Database (Shifts) samples
