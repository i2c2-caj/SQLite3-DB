"""
AUTHOR: COBY JOHNSON
PROJECT: SQLite3-DB
LAST UPDATE: 4/26/2014
VERSION: 0.2.1

DONE:
== Constructors / Destructors ==
+ DB.init (3/26/2014)

== Modify Table (Setters) ==
+ DB.createTable (3/27/2014)
+ DB.clearTable (4/1/2014)
+ DB.closeDB (3/27/2014)
+ DB.deleteRow (4/21/2014)
+ DB.dropTable (4/26/2014)
+ DB.insertRow (4/6/2014)
+ DB.updateRow

== Getters ==
+ DB.getColumnNames (4/22/2014)
+ DB.getConstraints
+ DB.getDBName (4/21/2014)
+ DB.getRow (4/22/2014)
+ DB.getTableNames (3/26/2014)
+ DB.getValues (4/28/2014)

== Utilities ==
+ DB.paramDict (4/21/2013)

TODO:
- [V 0.2.2] - Once all custom errors are done
    - unittest FOR ALL FUNCTIONS
        + port function Tests into unittests
    - Make Enums for paramdict 0,1,2,3
        + Maybe... TUPLE(0), COMMA(1), KEY(2), DEBUG(3)

- [V 0.2.3]
    - make a logging mode and a debugging mode module
        + logging mode will print each statement out to a file as they are executed
        + debugging mode will print each statement out to the console as they are executed
    - In try ... except clauses
        - Change them to print using paramDict option 3 to display actual dictionary values. It will help programmers
            debug issues easier

-!!!NEED TO MAKE ALL FUNCTIONS SAFE FROM SQL INJECTION ATTACKS!!!-

-MODIFY ALTER TABLE FUNCTION TO BE ABLE TO DROP TABLE AND RENAME COLUMNS BY:
    -HAVING IT COPY INFO TO NEW TABLE AND THEN RENAMING THE TABLE WHEN DROPPING A COLUMN
    -HAVING IT COPY INFO TO NEW TABLE BUT RENAME THE COLUMN THAT NEEDS TO BE RENAMED

"""

from errors import *
import sqlite3 as sql

OPERATORS = ['==', '!=', '<', '<=', '>', '>=']
TUPLE, COMMA, KEY, DEBUG = 0, 1, 2, 3

class DB:
    #__int__(self,
    #        name) #Name of the DB to be created
    def __init__(self, name=":memory:"):
        #Data members
        self.name = name.rstrip(".sql")
        #Load DB
        self.db = sql.connect(name)
        #Create DB cursor
        self.cursor = self.db.cursor()

    #createTable(self,
    #            table, #Table name
    #            info)  #(Column_name_1, ..., Column_name_X)
    def createTable(self, table, info):
        #print '''CREATE TABLE {0} {1}'''.format(table, info)
        try:
            self.cursor.execute('''CREATE TABLE {0} {1}'''.format(table, info))
            self.db.commit()
            return True
        except sql.OperationalError:
            if (table in self.getTableNames()):
                raise DuplicateTableError(table, self.getDBName())
            else:
                raise SyntaxError('''CREATE TABLE {0} {1}'''.format(table, info))
        
    #dropTable(self,
    #          table) #Table name
    def dropTable(self, table):
        #print '''DROP TABLE IF EXISTS {0}'''.format(table)
        try:
            self.cursor.execute('''DROP TABLE IF EXISTS {0}'''.format(table))
            self.db.commit()
            return True
        except sql.OperationalError as e:
            if ("syntax error" in str(e)):
                raise SyntaxError('''DROP TABLE IF EXISTS {0}'''.format(table))

    #clearTable(self,
    #           table) #Table name
    def clearTable(self, table):
        #print '''DELETE FROM {0}'''.format(table)
        try:
            self.cursor.execute('''DELETE FROM {0}'''.format(table))
            self.db.commit()
            #print 'Table ({0}) successfully cleared.'.format(table)
            return True
        except sql.OperationalError as e:
            if ("syntax error" in str(e)):
                raise SyntaxError('''DELETE FROM {0}'''.format(table))
            elif not (table in self.getTableNames()):
                raise TableDNE_Error(table, self.getDBName())

##    #alterTable(self,
##    #           table,   #Table
##    #           command) #SUPPORTS ADD column, RENAME TO table
##    ### NOTE: SQLITE3 DOES NOT SUPPORT: RENAME column, DROP column ###
##    def alterTable(self, table, command):
##        #print 'ALTER TABLE {0} {1}'.format(table, command)
##        self.cursor.execute('''ALTER TABLE {0} {1}'''.format(table, command))
##        self.db.commit()
##        return

    #insertRow(self,
    #          row,  #Row name
    #          info) #{key0:value0, ..., keyX:valueX}
    def insertRow(self, row, info):
        (keys, values) = self.paramDict(info)
        #print '''INSERT INTO {0} ({1}) VALUES ({2})'''.format(row, keys, values)
        try:
            self.cursor.execute('''INSERT INTO {0} ({1}) VALUES ({2})'''.format(row, keys, values), info)
            self.db.commit()
            return True
        #Syntax error or Table DNE
        except sql.OperationalError as e:
            if ("syntax error" in str(e)):
                raise SyntaxError('''INSERT INTO {0} ({1}) VALUES ({2})'''.format(row, keys, values))
            else:
                raise TableDNE_Error(row, self.getDBName())
        #Constraint violation
        except sql.IntegrityError as e:
            if ("constraint failed" in str(e)):
                raise ConstraintError('''INSERT INTO {0} ({1}) VALUES ({2})'''.format(row, keys, values), self.getConstraints(row)[0][2], row, self.getDBName())
            else:
                raise UniqueError('''INSERT INTO {0} ({1}) VALUES ({2})'''.format(row, keys, values), self.getConstraints(row)[0][1], row, self.getDBName())
        #Adapter missing
        except sql.InterfaceError as e:
            e = str(e)
            begin = e.find(':')
            end = e.find(' ', begin)
            var_name = e[begin+1:end]
            var_value = info[var_name]
            raise AdapterMissingError(var_value, row, self.getDBName())

    #deleteRow(self,
    #          row,       #Row name
    #          condition) #Condition to select data 
    def deleteRow(self, row, condition):
        query = self.paramDict(condition, 2)
        #print '''DELETE FROM {0} WHERE {1}'''.format(row, query)
        try:
            self.cursor.execute('''DELETE FROM {0} WHERE {1}'''.format(row, query), condition)
            self.db.commit()
            return True
        except sql.OperationalError as e:
            if ("no such table" in str(e)):
                raise TableDNE_Error(row, self.getDBName())
            elif ("no such column" in str(e)):
                e = str(e)
                begin = e.find(':') + 2
                column = e[begin:]
                raise ColumnDNE_Error(column, row, self.getDBName())
            elif ("syntax error" in str(e)):
                raise SyntaxError('''DELETE FROM {0} WHERE {1}'''.format(row, query))

    #getValues(self,
    #          row,       #Row name
    #          info,      #CSV string with columns to retrieve data from
    #          condition) #Dictionary of search requirements
    def getValues(self, row, info, condition):
        query = self.paramDict(condition, 2)
        print '''SELECT ({0}) FROM {1} WHERE {2}'''.format(info, row, query)
        try:
            self.cursor.execute('''SELECT {0} FROM {1} WHERE {2}'''.format(info, row, query), condition)
            result = self.cursor.fetchall()
            return result
        except sql.OperationalError as e:
            if ("no such column" in str(e)):
                e = str(e)
                begin = e.find(':') + 2
                column = e[begin:]
                raise ColumnDNE_Error(column, row, self.getDBName())
            elif ("syntax error" in str(e)):
                raise SyntaxError('''SELECT ({0}) FROM {1} WHERE {2}'''.format(info, row, query))
            elif ("no such table" in str(e)):
                raise TableDNE_Error(row, self.getDBName())

    #getRow(self,
    #       row,        #Row name
    #       condition)  #Dictionary of data involved in the query
    def getRow(self, row, condition):
        query = self.paramDict(condition, 2)
        #print '''SELECT * FROM {0} WHERE {1}'''.format(row, query)
        try:
            self.cursor.execute('''SELECT * FROM {0} WHERE {1}'''.format(row, query), condition)
            result = self.cursor.fetchall()
            return result
        except sql.OperationalError as e:
            if ("syntax error" in str(e)):
                raise SyntaxError('''SELECT * FROM {0} WHERE {1}'''.format(row, query))
            elif ("no such table" in str(e)):
                raise TableDNE_Error(row, self.getDBName())
            elif ("no such column" in str(e)):
                e = str(e)
                begin = e.find(':') + 2
                column = e[begin:]
                raise ColumnDNE_Error(column, row, self.getDBName())
            else:
                print type(e)
                print e

    #updateRow(self,
    #          row,        #Row name
    #          info,       #Dictionary of data involved in the query
    #          condition)  #Dictionary of a single item with a certain value to be found in DB
    def updateRow(self, row, info, condition):
        print self.paramDict(info)
        changes = self.paramDict(info, 1)
        (key, value) = self.paramDict(condition)
        print '''UPDATE {0} SET {1} WHERE {2}={3}'''.format(row, changes, key, value)
        self.cursor.execute('''UPDATE {0} SET {1} WHERE {2}={3}'''.format(row, changes, key, value), info)
        self.db.commit()
        return

    ##getTableNames(self)
    """
    Returns all table names in DB
    """
    def getTableNames(self):
        self.cursor.execute("select * from sqlite_master")
        schema = self.cursor.fetchall()
        tables = []
        for i in schema:
            if (i[0] == "table" and i[1] != "sqlite_sequence"):
                tables.append(str(i[1]))
        return tables

    #getColumnNames(self,
    #               table) #Table name
    """
    Returns all the columns name values from a table
    Returns in the format (tableName, [columnNames])
    """
    def getColumnNames(self, table):
        #Get table header from DB
        d = {'name': table}
        self.cursor.execute("select * from sqlite_master where name=(:name)", d)
        schema = self.cursor.fetchone()
        #Does the table exist?
        if (schema is None):
            raise TableDNE_Error(table, self.getDBName)
        #Find the parenthesis
        lp = schema[4].find('(') + 1
        rp = schema[4].rfind(')')
        #Type cast from unicode to string
        schema = str(schema[4])
        #Splice out the columnnames
        schema = schema[lp:rp]
        temp = schema.split(',')
        #Remove white space
        columns = []
        for item in temp:
            columns.append(item.strip())
        #pull names out and discard restraints
        names = []
        for n in columns:
            sp = n.find(' ')
            temp = n[:sp]
            names.append(temp)
        return (table, names)

    #paramDict(self,
    #          info,    #Dictionary to parse
    #          pair)    #Pair values (ie.key=:key) when true.
    """
    Parameterizes a dictionary into appropriate string values

    #db.insertRow()
    Return values look like this when pair = 0:
    key:    "key0, ..., keyX"
    values: ":key0, ..., :keyX"

    Rturn value looks like this when pair = 1:
    pairs = "key0=:key0, ... , keyX=:keyX"

    Return value looks like this when pair = 2:
    pairs = "key0<=:key0, key1!=:key1, ... , keyX<:keyX"

    Return value looks like this when pair = 3:
    pairs = "key0<=value0, key1!=value1, ... , keyX<valueX"


    """
    def paramDict(self, info, pair=0):
        if (pair == 0):
            keys = ""
            values = ""
            for k in info.keys():
                keys += k + ", "
                values += ":" + k + ", "
            keys = keys[:len(keys)-2]
            values = values[:len(values)-2]
            return (keys, values)
        elif (pair == 1):
            pairs = ""
            for k in info.keys():
                pairs += k + "=:" + k + ", "
            pairs = pairs[:len(pairs)-2]
            return pairs
        elif (pair == 2):
            pairs = ""
            for k in info.keys():
                if (str(type(info[k])) != "<type 'tuple'>"):
                    pairs += k +  "=:" + k + " AND "
                elif (info[k][0] in OPERATORS):
                    if (info[k][0] == '!='):
                        pairs += "NOT " + k + info[k][0][1] + ":" + k + " AND "
                    elif (info[k][0] == '=='):
                        pairs += k + info[k][0][1] + ":" + k + " AND "
                    else:
                        pairs += k + info[k][0] + ":" + k + " AND "
                    info[k] = info[k][1]
                else:
                    print '{0} is not a valid operator'.format(info[k][0])
            pairs = pairs[:len(pairs)-5]
            return pairs
        elif (pair == 3):
            pairs = ""
            for k in info.keys():
                if (type(info[k][1]) is str):
                    if (info[k][0] == '!='):
                        pairs += "NOT " + k + info[k][0][1] + '"' + info[k][1] + '" AND '
                    elif (info[k][0] == '=='):
                        pairs += k + info[k][0][1] + '"' + info[k][1] + '" AND '
                    else:
                        pairs += k + info[k][0] + '"' + info[k][1] + '" AND '
                else:
                    if (info[k][0] == '!='):
                        pairs += "NOT " + k + info[k][0][1] + str(info[k][1]) + " AND "
                    elif (info[k][0] == '=='):
                        pairs += k + info[k][0][1] + str(info[k][1]) + " AND "
                    else:
                        pairs += k + info[k][0] + str(info[k][1]) + " AND "
            pairs = pairs[:len(pairs)-5]
            return pairs

    #getConstraints(self,
    #               table) #Table name
    """
    Returns all the table columns that are under a unique/primary key restraint
    Returns in the format [(table_name, [column info]), ..., (table_name, [column info])]
    """
    def getConstraints(self, table="ALL"):
        
        #Find all constraints in all tables
        if (table == "ALL"):
            #Get all table headers from DB
            self.cursor.execute("select * from sqlite_master")
            schema = self.cursor.fetchall()
            #Pull out user created tables
            T = []
            for item in schema:
                if (item[0] == 'table' and item[1] != 'sqlite_sequence'):
                    T.append(item)
            #Pull out unique constraints for each table
            U = []
            for item in T:
                U.append(self.getConstraints(item[1])[0])
            return U

        #Find constraints in a specific table
        else:
            #Get table header from DB
            d = {'name': table}
            self.cursor.execute("select * from sqlite_master where name=(:name)", d)
            schema = self.cursor.fetchone()
            #Does the table exist?
            if (schema is None):
                raise TableDNE_Error(table, self.getDBName)
            #Find the parenthesis
            lp = schema[4].find('(') + 1
            rp = schema[4].rfind(')')
            #Type cast from unicode to string
            schema = str(schema[4])
            #Find table name before next step
            name = schema[:lp-1]
            temp = name.lower()
            n = temp.find('create table')
            name = name[n+12:].strip()
            #Splice out the columnnames
            schema = schema[lp:rp]
            temp = schema.split(',')
            #Remove white space
            columns = []
            for item in temp:
                columns.append((item.strip(), item.lower().strip()))
            #Pull out unique/primary key constraints and return
            unique = []
            check = []
            for item in columns:
                if (item[1].find('unique') != -1 or item[1].find('primary key') != -1):
                    unique.append(item[0])
                elif (item[1].find('check') != -1):
                    check.append(item[0])
            return [(name, unique, check)]

    #closeDB(self)
    def closeDB(self):
        try:
            #Save database
            self.db.commit()
            #Close cursor
            self.cursor.close()
            #Close database
            self.db.close()
            return True
        except sql.ProgrammingError:
            raise DBClosedError(self.getDBName())

    #getDBName(self)
    def getDBName(self):
        return self.name

def Tests(db):
    """
    Helper Methods
    """
    print db.paramDict({'Name': 'Test', "Number": 9, "Count": 20})
    print db.paramDict({'Name': 'Test', "Number": 9, "Count": 20}, 1)
    print db.paramDict({'Name': ('!=', 'Test'), "Number": ("==", 9), "Count": ("<", 20)}, 2)
    print db.paramDict({'Name': ('!=', 'Test'), "Number": ("==", 9), "Count": ("<", 20)}, 3)


##    """
##    DB Methods
##    """
##
##    #Get row
##    print db.getRow('MTG', {'name': 'Plain'})
##    print db.getRow('MTG', {'color': 'G'})
##
##    #Get values
##    print db.getValues('MTG', {'name': 'Plain', 'ID':  1, 'color': 'WH', 'count': 50}, {'ID': 1})
##    print db.getValues('MTG', {'name': 'Swamp', 'ID':  2, 'color': 'BK', 'count': 50}, {'color': 'BK'})
##
##    #Get Constraints
##    print db.getConstraints('MTG')
##    print db.getConstraints()
##
##    #Get column names
##    print db.getColumnNames('MTG')
##
##    #Print table
##    db.printTable('MTG')
##
##    #Update row
##    db.updateRow('MTG', {'count': 2000, 'color': 'IDK', 'ID': 3}, {'ID': 3})
##
##    #Clear table
##    db.clearTable('MTG')
##
##    #Clear table without asking
##    #db.clearTable('MTG', 1)
##
##    #Print table
##    db.printTable('MTG')

def main():
    db = DB()

    Tests(db)
    
    db.closeDB()

if __name__ == '__main__':
    main()
