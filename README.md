Lang: Python 3.9 / Win 10

# NCR Aloha POS to UCS Storehouse v4 Data Converter Utility.

Info:

- Aloha POS - https://www.ncr.com/restaurants/aloha-restaurant-pos-system
- Storehouse 4 - https://rkeeper.com/products/r_keeper/storehouse-5-skladskoy-uchet/
- Sample - https://www.youtube.com/watch?v=sJgA79ygrOg

Goal:

Get 'Aloha POS' (NCR) cash system data files:

1. Dictionary dbf-tables: CAT.DBF, CIT.DBF, CMP.DBF, ITM.DBF, TDR.DBF, RSN.DBF;
2. Shits dbf-tables: GNDITEM.DBF, GNDTNDR.DBF, GNDVOID.DBF;

Convert to 'Storehouse v4' data files: 

1. Dictionary dbf-tables: Categ.dbf, Expcateg.dbf, Goods.dbf, Gtree.dbf, sunits.dbf;
2. Shits dbf-table: Exp.dbf;

Run 'ImportRK' app for replicate data from converted dbf-files to sh4 database.

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

