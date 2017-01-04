'''
Created on 13/02/2014

@author: aecker
'''
from PyQt4.Qt import Qt
from PyQt4.QtCore import QAbstractTableModel, QModelIndex, QVariant
from PyQt4.QtGui import QColor 

from cx_Oracle import Connection

from app_const import PKEY_COL_CNT #, PKeyNextValue #, PKEY_VALUES

"""
    Raw Data
"""
class CounterKey(object):
    def __init__(self, resort = 'HMC', tsYear = 2014, tsWeek = 1):
        self.tsYear = tsYear
        self.tsWeek = tsWeek
        self.resort = resort


"""
    Qt Model definition
"""
class CountersModel(QAbstractTableModel):
    def __init__(self, config, parent = None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        #super(CountersModel, self).__init__(self, parent, *args)
        
        self.config = config
        self._counters = []
        self.pkeyAndCounterColumnNames = '' #None
        """
        self._modified = False
        self._sourceRowForNextAdd = -1
        self.dataChanged.connect(self._dataModified)
        """ 
    
    def putRsYrWk(self, pkey, row = None, rows = None):      # pkey is tuple of (resort, tsYear, tsWeek)
        ret = False
        if not row:
            row = len(self._counters)
        if not rows:
            rows = 1
        if pkey[0][0] == '-':
            pkey[0] = pkey[0][1:]
            #itm = filter(lambda i: i['pkey'] == pkey, self._counters)
            #if itm:
            #    row = self._counters.index(itm)
            row = ( [i for i in range(len(self._counters)) if self._counters[i]['pkey'] == pkey] or [-1] )[0]
            if row >= 0:
                self.beginRemoveRows(QModelIndex(), row, row + rows - 1)
                self._counters.pop(row)
                self.endRemoveRows()
                ret = True
        else:
            self.beginInsertRows(QModelIndex(), row, row + rows - 1)
            for _ in range(rows):
                if not filter(lambda i: i['pkey'] == pkey, self._counters):
                    dbRow = self.fetchWeekCounters(pkey[0], pkey[1], pkey[2])
                    self._counters.insert(row, dict(pkey = pkey, counters = dbRow[PKEY_COL_CNT:]))
                    ret = True
            self.endInsertRows()
        return ret
         
                                  
    """
         Database handling
    """
    
    def fetchWeekCounters(self, resort = 'HMC', yr = 2014, wk = 1):
        """
        def OutputTypeHandler(cursor, name, defaultType, size, precision, scale):
            print cursor, name, defaultType, size, precision, scale
            if defaultType in (cx_Oracle.STRING, cx_Oracle.FIXED_CHAR):
                return cursor.var(unicode, size, cursor.arraysize)
        """
        connection = Connection(self.config.get("main", "DbConnect"))
        #connection.outputtypehandler = OutputTypeHandler
        
        cursor = connection.cursor()
        cursor.execute('select * from V_RESL_BOOKING_COUNTERS where "Resort" = :resort and "TSYear" = :yr and "TSWeek" = :wk', resort = resort, yr = yr, wk = wk)
        row = cursor.fetchone()
        if not self.pkeyAndCounterColumnNames:
            self.pkeyAndCounterColumnNames = [i[0] for i in cursor.description]
            
        connection.close()
        
        return row
    
        
    def refreshFromDb(self):
        from operator import add, sub
        diffs = [0 for _ in range(len(self.pkeyAndCounterColumnNames) - PKEY_COL_CNT)]
        self.beginResetModel()
        for c in self._counters:
            row = self.fetchWeekCounters(c['pkey'][0], c['pkey'][1], c['pkey'][2])
            diffs = map(add, diffs, map(sub, row[PKEY_COL_CNT:], c['counters']))     # sum(diffs = newVals - oldVals)
            c['counters'] = row[PKEY_COL_CNT:]
        self.endResetModel()
        diffStatus = [self.pkeyAndCounterColumnNames[PKEY_COL_CNT + nI] + ": " + '{0:+}'.format(diffs[nI]) for nI in range(len(diffs)) if diffs[nI] <> 0]
        return ", ".join(diffStatus) if diffStatus else ""

               
    """
        Qt model interface
    """
    def rowCount(self, parent = None):  # changed to allow parent as opt param
        return len(self._counters)
    def columnCount(self, parent):
        return len(self.pkeyAndCounterColumnNames)
        
    def headerData(self, section, orientation, role):
        ret = None
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            ret = self.pkeyAndCounterColumnNames[section]
        return ret

    def data(self, index, role):
        ret = None
        if role == Qt.TextAlignmentRole:
            ret = Qt.AlignTrailing | Qt.AlignVCenter if index.column() >= PKEY_COL_CNT else Qt.AlignCenter
        elif role == Qt.DisplayRole and index.isValid():
            row = index.row()
            if row in range(len(self._counters)):
                col = index.column()
                if col < PKEY_COL_CNT:
                    ret = self._counters[row]['pkey'][col]
                elif col >= PKEY_COL_CNT and col < len(self.pkeyAndCounterColumnNames):
                    ret = self._counters[row]['counters'][col - PKEY_COL_CNT]
        elif role == Qt.BackgroundColorRole:     # PyQt4 also works with role == Qt.BackgroundRole
            row = index.row()
            col = index.column()
            if col >= PKEY_COL_CNT:
                val = int(self._counters[row]['counters'][col - PKEY_COL_CNT])
                threshold = int(self.config.get(self._counters[row]['pkey'][0] + '-OccThresholds', self.pkeyAndCounterColumnNames[col].replace(' ', '')))
                ret = QColor(max(0, min(255, int(255 * val / threshold))), max(0, min(255, int(255 * (1 - val / threshold)))), 0, 69)   # 69 is alpha/transparency
        elif role == Qt.ToolTipRole:
            row = index.row()
            col = index.column()
            if col >= PKEY_COL_CNT:
                ret = self.pkeyAndCounterColumnNames[col] \
                    + " threshold: " + self.config.get(self._counters[row]['pkey'][0] + '-OccThresholds', self.pkeyAndCounterColumnNames[col].replace(' ', ''))
            
            
        return QVariant(ret)

    def setData(self, index, value, role):
        ret = False
        """
        if index.isValid():
            row = index.row()
            col = index.column()
            ckeys = self._counters.keys()   # for indexing
            if col < PKEY_COL_CNT and role == Qt.EditRole:
                self._counters.pop(ckeys[row])
                ckey = list(ckeys[row])     # change primary key tuple of current counters row
                ckey[col] = PKEY_VALUES[col][value.toInt()[0]]  # .. only one of the PKEY_COL_CNT columns/values
                self.putRsYrWk(ckey)
            self.dataChanged.emit(index, index)
            ret = True
        """
        return ret

    def flags(self, index):
        if index.isValid():
            ret = QAbstractTableModel.flags(self, index)
            ret = ret | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            """
            col = index.column()
            if col < PKEY_COL_CNT:
                ret = ret | Qt.ItemIsEditable
            """
        else:
            ret = Qt.ItemIsEnabled
        return ret

    """    
    def insertRows(self, row, rows, parent):
        return self.putRsYrWk(PKeyNextValue(self._counters[row]['pkey']), row, rows)
    def removeRows(self, row, rows, parent):
        self.beginRemoveRows(QModelIndex(), row, row + rows - 1)
        for _ in range(rows):
            self._counters.pop(row)
        self.endRemoveRows()
        return True
    """






""" PyQt4's QSql is missing qsqloci4.dll in C:\Python27\Lib\site-packages\PyQt4\plugins\sqldrivers

#ERROR message on run:
#
#QSqlDatabase: QOCI driver not loaded
#QSqlDatabase: available drivers: QSQLITE QMYSQL3 QMYSQL QODBC3 QODBC QPSQL7 QPSQL
#QSqlQuery::exec: database not open


import sys

from PyQt4.QtGui import QApplication
from PyQt4.QtSql import QSqlDatabase, QSqlQuery

app = QApplication(sys.argv)

#db = QSqlDatabase()
db = QSqlDatabase.addDatabase("QOCI")
#db.setHostName("SP.DEV");
db.setDatabaseName("SP.DEV");
db.setUserName("AECKER")
db.setPassword("oschoens")
db.setPort(1521)
#db.setConnectOptions("CLIENT_SSL=1;CLIENT_IGNORE_SPACE=1")
ok = db.open()

query = QSqlQuery("select * from T_LU")
ok = query.exec_()
while query.next():
    print query.value(4)
    print query.record()

db.close()
"""



"""
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text='Hello World')

TestApp().run()
"""

"""
DB access in kivy - copied from kivy user blog (see email https://mail.google.com/mail/?ui=2&shva=1#inbox/1441b45fc2a09cdc):

def write_order_header(warehouse, rowid):
    with ConnectionToDB(True) as connection:
        connection.cursor.execute('SELECT IFNULL(SUM(sum_all), 0) FROM docstable WHERE id = ?', (rowid,))
        
        summ = connection.cursor.fetchall()[0][0]
        connection.cursor.execute('UPDATE docs SET total = ?, status = "ready" WHERE id = ?', (summ, rowid))

        # refreshing stocks after order is complete
        connection.cursor.execute('''SELECT DISTINCT
                                        tmc.name, tmc.quantity, docstable.quantity
                                    FROM tmc
                                    LEFT JOIN docstable ON docstable.tmc = tmc.name
                                    WHERE
                                        docstable.id = ?''', (rowid,))

        for row in connection.cursor:
            connection.cursor.execute('UPDATE tmc SET quantity = ? WHERE warehouse = ? AND name = ?',
                                      (max(row[1]-row[2], 0), warehouse, row[0]))
    connection.conn.commit()
"""