#!usr/bin/env python
# -*- coding: utf-8 -*-

from database import JSONDB

if __name__=="__main__":
    shopDb = JSONDB('shop_db',hashSize=1)  #create shop db
    userDb = JSONDB('sellerDb',hashSize=1) #create user db

    #specify key
    shopDb.ensureKey('shop',['id'])
    shopDb.ensureKey('goods',['id'])
    userDb.ensureKey('seller',['id','name'])
    userDb.ensureKey('customer',['id','name'])

    #for debugging, you can start perfDot and open debug switch
    shopDb.perfDotStart()
    userDb.perfDotStart()
    shopDb.debugSwitch(1)
    userDb.debugSwitch(1)

    #insert data
    #here we insert some data

    for i in range(0,100):
        #insert data one by one
        shopDb.insert('shop',[{'id':i, 'name':'my shop', 'description':'this is a telephone shop'}])

    #inset a data list
    goodsList = [{'id':10001, 'class':'telephone', 'brand':'apple', 'color':'white'},
                 {'id':10002, 'class':'telephone', 'brand':'huawei', 'color':'black'},
                 {'id':10003, 'class':'telephone', 'brand':'zte', 'color':'white'},
                 {'id':10004, 'class':'telephone', 'brand':'xiaomi', 'color':'black'},
                 {'id':10005, 'class':'telephone', 'brand':'moto', 'color':'white'},
                 {'id':10006, 'class':'telephone', 'brand':'oppo', 'color':'black'},]
    shopDb.insert('goods',goodsList)

    sellersList = [{'id':0x34200,'name':'li','sex':'female','birth':'1985-09-03','tel':'0816-19876545432'},
                   {'id':0x34201,'name':'wang','sex':'male','birth':'1988-11-03','tel':'0816-2345453453'},
                   {'id':0x34202,'name':'hong','sex':'female','birth':'1995-10-19','tel':'0816-144567589'}]
    userDb.insert('seller',sellersList)

    customersList = [{'id':0x7800,'name':'zhu','sex':'female','profile':['dress','mother','sport']},
                   {'id':0x7801,'name':'rong','sex':'male','profile':['baby','read','tech']},
                   {'id':0x7802,'name':'guo','sex':'female','profile':['phone','dress','food']}]
    userDb.insert('customer',customersList)

    #export to default file
    shopDb.exportToFile()
    userDb.exportToFile(fileName='user')

    #find
    # find with key
    findList = shopDb.find('goods',filter={'id':{'$lt':10004}})
    JSONDB.rprint(findList)
    findList = shopDb.find('goods',filter={'id':10004})
    JSONDB.rprint(findList)
    findList = userDb.find('customer',filter={'name':'guo'})
    JSONDB.rprint(findList)

    #delete
    shopDb.delete('goods',{'id':10005})

    #update
    shopDb.update('goods',set={'class':'phone'})


    #merge
    shopDb.merge(userDb)
    shopDb.exportToFile('mergeDb')

    #show pref time
    shopDb.perfDotEnd()
    userDb.perfDotEnd()

    #import
    importDb = JSONDB('importDb')
    importDb.debugSwitch(1)
    importDb.importFromFile(fileName='mergeDb')
    #importDb.printAll()
    importDb.exportToFile()

    print importDb

