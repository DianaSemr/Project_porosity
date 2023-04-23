import cv2
import sqlite3
import numpy as np
import PIL.Image as Img
import PIL.ImageEnhance as Enhance


rows = [
    (0, 'Материал2', 12.0, 5.0, 0.1, 0.01),
    (1, 'Материал3', 9.00, 8.0, 0.15, 0.01),
    (2, 'Материал4', 15.0, 8.0, 0.2, 0.5),
    (3, 'Материал5', 14.0, 7.0, 0.3, 0.7),
    ]
conn = sqlite3.connect("my_database.db")
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS Materials')
cur.execute("""CREATE TABLE Materials (ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,                                        NAME TEXT, 
                                       PORE_AREA_MEAN REAL NOT NULL,              
                                       PORE_AREA_STD REAL NOT NULL, 
                                       POROUS_MEAN REAL NOT NULL,                                        
                                       POROUS_STD REAL NOT NULL )""")
cur.executemany("""INSERT INTO Materials values (?,?,?,?,?,?)""", rows)
cur.execute('SELECT * FROM Materials')
#print(cur.fetchall())
conn.commit()
conn.close()
