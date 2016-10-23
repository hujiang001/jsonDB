#!usr/bin/env python
#  -*- coding: utf-8 -*-
"""
Author: hujiang001@gmail.com
ChangeLog: 2016-10-01 created
description:
    jsonDB是一个基于JSON格式的内存数据库.它具有以下特点:
    1\轻量级. 无守护进程,无需任何额外的安装和配置,你只需要import jsonDb即可使用,非常方便.
    2\NOSQL. 类似于mongoDb的非关系型数据库.
    3\内存数据库. 所有数据基于内存进行操作和访问,性能相对较高.目前版本的性能测试数据请
    参考reference文档.
    4\任意迁移. 数据库可以完整导出为外部文件,并且可以从外部文件导入.基于此,数据库可以
    进行任意的迁移,而无需做任何修改.
    5\灵活的数据类型. 一个数据集合(collection)中的数据,并不需要相同的格式.比如以下几种数据
    可以同时存在于一个collection中:
    {'key1':1},{'key2':'value','pic':'value'},{'key3':'value'}

    ** 概念说明:
    1\db: 即数据库. 创建一个jsonDb类的实例,即是创建了一个数据库.可以指定dbname和hash的长度.
    2\collection: 数据集合(表). 一个collection可以理解为数据库中的一个表. collection不需要
      单独创建,当insert第一条数据,或者ensureKey时,系统会自动创建.
    3\data: 数据. collection中的一条数据,或者是一个数据的list. data必须是dict字典类型,是一个
    key-value键值对.

    ** 支持的功能:
    数据插入
    数据删除
    数据更新
    数据查询(支持丰富的条件查询)
    指定key值(支持key值hash查找,提高效率)
    数据库合并
    导出数据库到外部文件
    从外部文件导入数据库
    关键过程性能打点(毫秒级耗时统计)
    数据库统计显示(包括数据规模\占用内存等)
    格式化打印

    ** 关键词说明:
    以下关键词属于系统保留,不能作为任何字典dict的key名.
    $lt $lte $gt $gte $ne $or $or[0-9]
    $jdb $jdb_collections $jdb_key $jdb_hash $jdb_coll $jdb_hashSize $jdb_md5

LICENCE: The MIT License (MIT)

Copyright (c) [2016] [iotX]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import copy
import re
import os



class JSONDB:
    __g_memDb = {}
    __g_debug_open = 0 #close as default
    __g_lock = 0 #1:locked 2:unlocked
    __g_perfDot = {'sw':False}

    def __init__(self, dbName, hashSize=1000):
        '''
        :param dbName:db的名字
        :param hashSize:hash表的大小
        :return:
        '''
        self.__createDb(dbName,hashSize)

    def __perfDotDeco(dotName, prefDot):
        '''
        性能打点的装饰器
        :param dotName: 打点名称,任意定义的字符串
        :return:
        '''
        def _perfDot(func):
            def __perfDot(*args, **kwargs):
                if prefDot['sw'] == True:
                    import time
                    now = time.time()

                ret = func(*args, **kwargs)

                if prefDot['sw'] == True:
                    if not prefDot.has_key(dotName):
                        prefDot[dotName] = 0
                    prefDot[dotName] += time.time()-now

                return ret
            return __perfDot
        return _perfDot

    def __debug(self, str):
        if self.__g_debug_open == 1:
            print(str)

    def __getLock(self):
        if self.__g_lock == 1:
            self.__debug('db is locked, try later!')
            return False
        self.__g_lock = 1
        return True

    def __putLock(self):
        self.__g_lock =0

    def __createDb(self, dbName, hashSize=1000):
        self.__g_memDb = {'$jdb':dbName,
                          '$jdb_collections':[],
                          '$jdb_hashSize':hashSize}
    def __status(self):
        '''
        打印当前数据库的状态统计
        db_name - 数据库名
        mem_collection - collection消耗的总内存
        mem_hash - hash表消耗的总内存
        collection_num - collection个数
        collection_staus - 分别显示每个collection的data条数\key等信息
        :return:
        '''
        import sys
        status = {'db_name':'','mem_collection':0,'mem_hash':0,'collection_num':0,'collection_staus':[]}
        status['db_name'] = self.__g_memDb['$jdb']
        status['collection_num'] = len(self.__g_memDb['$jdb_collections'])
        colls = self.findCollection()
        for item in colls:
            colStatus = {'name':item, 'data_num':0,
                         'index':False, 'key':[],
                         'data_mem':0, 'hash_mem':0}
            col = self.__coll(item)
            status["mem_collection"] += sys.getsizeof(col[col['$jdb_coll']])
            colStatus['data_mem'] = sys.getsizeof(col[col['$jdb_coll']])
            if col.has_key('$jdb_hash'):
                colStatus['index'] = True
                colStatus['key'].extend(col['$jdb_key'])
                colStatus['data_num'] = len(col[col['$jdb_coll']])
                colStatus['name'] = col['$jdb_coll']
                status['mem_hash'] += sys.getsizeof(col['$jdb_hash'])
                colStatus['hash_mem'] = sys.getsizeof(col['$jdb_hash'])
            status['collection_staus'].append(colStatus)

        #print
        ret= '\n------ jdb statics ------'
        ret+= '\ndb_name: '+status['db_name']
        ret+= '\nmem_collection: '+str(status['mem_collection'])+' bytes'
        ret+= '\nmem_hash: '+str(status['mem_hash'])+' bytes'
        ret+= '\ncollection_num: '+str(status['collection_num'])
        ret+= '\n**** collection statics **** '
        for s in status['collection_staus']:
            ret+= '\n name: '+s['name']
            ret+= '\n data_num: '+str(s['data_num'])
            ret+= '\n key: '+str(s['key'])
            ret+= '\n index: '+str(s['index'])
            ret+= '\n data_mem: '+str(s['data_mem'])+' bytes'
            ret+= '\n hash_mem: '+str(s['hash_mem'])+' bytes'
            ret+= '\n'
        return ret
    #以下json的代码用于解决json.load后转换为unicode的问题
    def __json_load_byteified(self,file_handle):
        return self.__byteify(
                json.load(file_handle, object_hook=self.__byteify),
                ignore_dicts=True
        )

    def __json_loads_byteified(self, json_text):
        return self.__byteify(
                json.loads(json_text, object_hook=self.__byteify),
                ignore_dicts=True
        )

    def __byteify(self, data, ignore_dicts = False):
        # if this is a unicode string, return its string representation
        if isinstance(data, unicode):
            return data.encode('utf-8')
        # if this is a list of values, return list of byteified values
        if isinstance(data, list):
            return [ self.__byteify(item, ignore_dicts=True) for item in data ]
        # if this is a dictionary, return dictionary of byteified keys and values
        # but only if we haven't already byteified it
        if isinstance(data, dict) and not ignore_dicts:
            return {
                self.__byteify(key, ignore_dicts=True): self.__byteify(value, ignore_dicts=True)
                for key, value in data.iteritems()
                }
        # if it's anything else, return it in its original form
        return data

    def __getHash(self, key):
        '''
        hash key生成算法
        对于字符串,将字符串中的每个字节循环乘以33累加:
        for (i=0; i<key.length(); ++i) hash = 33*hash + key.charAt(i);
        对于数字,不做处理.
        然后将所有key项累加,最后的总和根据hash表的长度取模.
        只支持整形和字符串,其它返回错误.
        '''
        tmpStrSum = 1
        sum = 0
        if type(key) is not dict:
            return None
        for item in key.values():
            strTmp = str(item)
            for i in range(0,len(strTmp)):
                tmpStrSum = 33*tmpStrSum + ord(strTmp[i])
            sum = sum + tmpStrSum

        return sum%self.__g_memDb['$jdb_hashSize']

    def __coll(self, collName):
        for coll in self.__g_memDb['$jdb_collections']:
            if coll.has_key(collName):
                return coll
        return None

    def __collName(self, collName):
        result = []
        for coll in self.__g_memDb['$jdb_collections']:
            if collName is None:
                result.append(coll['$jdb_coll'])
            else:
                if coll.has_key(collName):
                    result.append(collName)
                    return result
        return result

    def __filterCondCheck(self, x, filter):
        '''
        等于	        {<key>:<value>}
        小于     	{<key>:{$lt:<value>}}
        小于或等于	{<key>:{$lte:<value>}}
        大于	        {<key>:{$gt:<value>}}
        大于或等于	{<key>:{$gte:<value>}}
        不等于    	{<key>:{$ne:<value>}}
        '''
        if type(filter) is not dict: #等于
            if x == filter:
                return True
        else:
            if filter.has_key('$lt'): #小于
                if x < filter['$lt']:
                    return True
            elif filter.has_key('$lte'):#小于或等于
                if x <= filter['$lte']:
                    return True
            elif filter.has_key('$gt'):#大于
                if x > filter['$gt']:
                    return True
            elif filter.has_key('$gte'):#大于或等于
                if x >= filter['$gte']:
                    return True
            elif filter.has_key('$ne'):#不等于
                if x != filter['$ne']:
                    return True
            else:
                return False
        return False

    def __filterDoRecursive(self, data, filter, isOr=0):
        '''
        支持同时携带多个key-value条件,
        例如:
        各个key-value之间是AND关系{<key1>:<value1>, <key2>:{$lt:<value2>}, ......}
        各个key-value之间是OR关系{'$or':{<key1>:<value1>, <key2>:{$lt:<value2>}, ......}}
        可以组合使用{<key1>:<value1>, '$or':{<key2>:<value2>, <key3>:{$lt:<value3>}}}
        如果有多个or条件,关键字可以使用'$or1'\'$or2'\'$or3'\...
        该函数通过递归方式实现
        '''
        ret = False
        for key in filter.keys():
            ret = True
            if re.match('''^\$or[0-9]*$''',key) is not None:
                ret = self.__filterDoRecursive(data,filter[key],isOr=1)
            else:
                if not data.has_key(key):
                    ret = False
                if self.__filterCondCheck(data[key], filter[key]) is False:
                    ret = False
            if isOr == 1:
                if ret == True:
                    return True
            else:
                if ret == False:
                    return False

        if isOr == 1:
            return False
        else:
            return True


    def __filterDo(self, data, filter):
        if len(filter.keys()) == 0:
            return True
        #第一次调用,条件之间应该是AND关系
        return self.__filterDoRecursive(data,filter,isOr=0)

    def __isCondFilter(self, filter):
        '''
        判断是否是条件查询,条件查询包含以下关键词:
        $lt $lte $gt $gte $ne $or $or[0-9]
        '''
        keywords = ['$lt','$lte','$gt','$gte','$ne','$or']
        for w in keywords:
            if str(filter).find(w) != -1:
                return True
        return False

    def __findInColl(self, coll, filter=None, limit=0, deepcpy=1):
        retList = []
        #如果是key值查找,那么直接从hash表查找
        if coll.has_key('$jdb_key') \
                and filter is not None \
                and coll['$jdb_key']==filter.keys() \
                and not self.__isCondFilter(filter):#不能是条件查找
            if deepcpy == 1:
                tmpV = copy.deepcopy(self.__hashFind(filter,coll))
            else:
                tmpV = self.__hashFind(filter,coll)
            retList.append(tmpV)
            return retList
        #其它需要遍历
        if deepcpy == 1:
            dataList = copy.deepcopy(coll[coll['$jdb_coll']]) #这里应该deepcopy,避免用户修改数据库内容
        else:
            dataList = coll[coll['$jdb_coll']]

        if filter is None:
            retList = dataList
        else:
            for data in dataList:
                if self.__filterDo(data, filter) is True:
                    retList.append(data)
        if limit == 0:
            return retList
        else:
            return retList[0:limit]

    def __compKey(self, key, data):
        for k in key:
            if data[k]!=key[k]:
                return False
        return True

    def __hashFind(self, key, coll):
        index = self.__getHash(key)
        nodes = coll['$jdb_hash'][index]
        flag = False
        for node in nodes:
            if self.__compKey(key,node) is True:
                return node
        return None

    def __find(self, collection=None, filter=None, limit=0, deepcpy=1):
        result = []
        numLeft = limit
        if collection is None:
            for coll in self.__g_memDb['$jdb_collections']:
                findList = self.__findInColl(coll, filter, numLeft, deepcpy)
                if findList is not []:
                    result.extend(findList)
                    if limit != 0:
                        if limit > len(result):
                            numLeft = limit - len(result)
                        else:
                            return result
            return result

        if self.__coll(collection) is None:
            return []

        coll = self.__coll(collection)
        return self.__findInColl(coll,filter,limit,deepcpy)

    def __hashAdd(self, dataPtr, coll):
        #key
        tmpKey = {}
        for key in coll['$jdb_key']:
            tmpKey[key] = dataPtr[key]
        index = self.__getHash(tmpKey)
        coll['$jdb_hash'][index].append(dataPtr)
        return True

    def __hashRemove(self, data, coll):
        #key
        tmpKey = {}
        for key in coll['$jdb_key']:
            tmpKey[key] = data[key]
        index = self.__getHash(tmpKey)
        nodes = coll['$jdb_hash'][index]
        for node in nodes:
            if self.__compKey(tmpKey,node) is True:
                nodes.remove(node)
                return
        return

    def __judgeKeyConflict(self, coll, dataList):
        tmpKey = {}
        keyList = coll['$jdb_key']
        #key必须都包含
        for key in keyList:
            for data in dataList:
                if not data.has_key(key):
                    self.__debug('key error, key is '+str(keyList)+ \
                                 ', your data is '+str(data))
                    return False
                tmpKey[key] = data[key]

            #key保证唯一性
            if self.__hashFind(tmpKey, coll) is not None:
                self.__debug('key confilct, data is '+str(data))
                return False
        return True

    def __insert(self, collection, data, isMerge):
        if type(data) is not list:
            self.__debug('data is not list type')
            return False

        #merge()调用过来的,不需要获取锁
        #使用调用栈的方式太耗性能
        #if inspect.stack()[1][3]!='merge':
        if isMerge!=1:
            if not self.__getLock():
                return False

        oldLen = 0 #原来coll的list长度,用于计算新增data的index
        #这里不能使用list.index(),性能非常低
        coll = self.__coll(collection)
        if coll is not None:
            #检查key是否冲突
            if coll.has_key('$jdb_key') \
                    and not self.__judgeKeyConflict(coll,data):
                if isMerge!=1:
                    self.__putLock()
                return False
            oldLen = len(coll[collection])
        else:
            oldLen = 0
            self.__g_memDb['$jdb_collections'].extend([{collection:[],'$jdb_coll':collection}])

        coll = self.__coll(collection)
        coll[collection].extend(data)
        #添加到hash表
        if coll.has_key('$jdb_key'):
            for item in data:
                self.__hashAdd(coll[coll['$jdb_coll']][oldLen],coll)
                oldLen += 1

        #if inspect.stack()[1][3]!='merge':
        if isMerge!=1:
            self.__putLock()

        return True

    def debugSwitch(self, switch):
        '''
        debug开关
        :param switch:debug开关,1:open 0:close
        :return:
        '''
        self.__g_debug_open = switch

    def perfDotStart(self):
        '''
        开启性能打点,支持insert\update\find\delete\export to file\import to file
        等关键流程的耗时统计.
        注意这里的统计是perfDotStart到perfDotEnd之间这些操作的累计值.
        比如,期间多次调用insert操作,那么insert的耗时是所有这些的累计值.
        :return:
        '''
        self.__g_perfDot['sw']=True

    def perfDotEnd(self):
        '''
        结束性能打点,并且打印结果
        '''
        print '------ perf dot statics ------'
        for key in self.__g_perfDot:
            if key=='sw':
                continue
            print '['+key+']''spend time: '+str(self.__g_perfDot[key])
        print ''

        self.__g_perfDot['sw']=False
        #init
        keys = self.__g_perfDot.keys()
        for k in keys:
            if k!='sw':
                self.__g_perfDot.pop(k)

    '''
    indent = 1, 格式化输出
    '''
    @staticmethod
    def rprint(data, indent=0):
        '''
        格式化打印
        :param data:需要打印的数据,必须是json格式
        :param indent:1-优化的打印格式,0-不做优化
        :return:
        '''
        print json.dumps(data,indent=indent)

    def printAll(self):
        self.rprint(self.__g_memDb,indent=1)

    @__perfDotDeco('insert',__g_perfDot)
    def insert(self, collection, data):
        '''
        插入数据
        :param collection:数据集的名字
        :param data:需要插入的数据,必须是list.即使插入一条数据,也需要是list格式.
        例如: [data1,data2,data3],每个data则建议使用字典格式.
        例如: data1 -  {'key':'xx','id':1}
        :return:
        '''
        return self.__insert(collection,data,0)

    @__perfDotDeco('delete',__g_perfDot)
    def update(self, collection, set, filter=None):
        '''
        更新数据
        :param collection: 指定更新的collection,不支持多个collection,不能为None.
        :param set: 更新的内容.是一个dict类型.
        :param filter: 参考find()中的定义
        :return:
        '''
        if not self.__getLock():
            return False
        #不支持一次更新多个collection
        if collection is None:
            self.__putLock()
            return False
        coll = self.__coll(collection)
        if coll is None:
            self.__putLock()
            return False
        findList = self.__find(collection,filter,0,0)
        if len(findList) == 0:
            self.__putLock()
            return False
        #update
        for item in findList:
            for key in set.keys():
                item[key] = set[key]

        self.__putLock()
        return True

    @__perfDotDeco('delete',__g_perfDot)
    def delete(self, collection, filter=None):
        '''
        删除数据
        :param collection:指定删除的collection,不支持多个collection,不能为None.
        :param filter:参考find()中的定义
        :return:
        '''
        if not self.__getLock():
            return False
        #不支持一次删除多个collection
        if collection is None:
            self.__putLock()
            return False
        coll = self.__coll(collection)
        if coll is None:
            self.__putLock()
            return False
        findList = self.find(collection,filter)
        if len(findList) == 0:
            self.__putLock()
            return False
        for item in findList:
            #从hash表中删除
            if coll.has_key('$jdb_key'):
                self.__hashRemove(item,coll)
            coll[collection].remove(item)

        self.__putLock()
        return True

    @__perfDotDeco('find',__g_perfDot)
    def find(self, collection=None, filter=None, limit=0):
        '''
        查询
        :param collection:指定查询的collection.None表示在所有collection中查询.
        :param filter:过滤条件.
        等于	        {<key>:<value>}
        小于     	{<key>:{'$lt':<value>}}
        小于或等于	{<key>:{'$lte':<value>}}
        大于	        {<key>:{'$gt':<value>}}
        大于或等于	{<key>:{'$gte':<value>}}
        不等于    	{<key>:{'$ne':<value>}}
        支持同时携带多个key-value条件,
        例如:
        各个key-value之间是AND关系{<key1>:<value1>, <key2>:{$lt:<value2>}, ......}
        各个key-value之间是OR关系{'$or':{<key1>:<value1>, <key2>:{$lt:<value2>}, ......}}
        可以组合使用{<key1>:<value1>, '$or':{<key2>:<value2>, <key3>:{$lt:<value3>}}}
        如果有多个or条件,关键字可以使用'$or1'\'$or2'\'$or3'\...,范围'$or[0-9]'
        :param limit:返回结果的个数限制.0 - 无限制
        :return:结果list,list中包含了所有匹配的data.需要注意的是,list中不包含collection名.
        '''
        return self.__find(collection,filter,limit,1)

    @__perfDotDeco('merge',__g_perfDot)
    def merge(self, dbObj):
        '''
        数据库合并,将dbObj合并到本数据库中来.
        collection的key定义不同,不能进行merge.
        :param dbObj: 需要合并的数据库对象.type(dbobj) is jsonDb.
        :return:
        '''
        if not self.__getLock():
            return False
        if not isinstance(dbObj, JSONDB):
            self.__debug("dbObj is not instance of jsonDb")
            self.__putLock()
            return False
        '''
        这里不能直接将dbObj中的数据拷贝过来,而是要遍历执行insert流程.因为有些数据可能
        存在冲突. 为了冲突时好回退,我们不直接操作__g_memDb,而是拷贝一个临时数据库,完全
        成功后再覆盖过去.
        '''
        tmpDb = copy.deepcopy(self.__g_memDb) #deepcopy

        for coll in dbObj.__g_memDb['$jdb_collections']:
            #如果定义了key,那么key必须一致
            myColl = self.__coll(coll['$jdb_coll'])
            if coll.has_key('$jdb_key'):
                if myColl is None:
                    self.ensureKey(coll['$jdb_coll'], coll['$jdb_key'])
                else:
                    if myColl.has_key('$jdb_key'):
                        if myColl['$jdb_key'] != coll['$jdb_key']:
                            return False
                    else:
                        return False
            else:
                if myColl is not None \
                        and myColl.has_key('$jdb_key'):
                    return False
            #hash结构在insert过程中自动生成
            if not self.__insert(collection=coll['$jdb_coll'], data=coll[coll['$jdb_coll']], isMerge=1):
                #rollback
                self.__debug('merge failed for insert fail')
                self.__g_memDb = copy.deepcopy(tmpDb)
                self.__putLock()
                return False

        self.__putLock()
        return True

    def findCollection(self, collection=None):
        '''
        查询collection,会返回一个只包含collection name的list.该功能可以用来查询一个
        collection是否存在.
        :param collection: 指定collection name,None-所有collection
        :return:
        '''
        return copy.deepcopy(self.__collName(collection))

    @__perfDotDeco('import from file',__g_perfDot)
    def importFromFile(self, fileName=None, path='./db/'):
        '''
        从外部文件中导入数据,该文件应该是通过exportToFile导出的文件.
        首先会校验文件的合法性,如果文件不完整或者不是exportToFile导出的,则无法导入.
        外部导入的数据将通过merge(),合入到当前的db中.
        :param fileName:文件名,如果为None,那么文件名默认为在init时指定的dbName.
        :param path:文件路径,默认为'./db/'
        :return:
        '''
        if fileName is None:
            fileName = self.__g_memDb['$jdb']
        if not os.path.exists(path+fileName):
            return False
        tmpDb = JSONDB('tmpDb')
        fp = open(path+fileName,'r')
        tmpDb.__g_memDb = self.__json_load_byteified(fp)
        fp.close()
        #校验文件的合法性
        md5InFile = tmpDb.__g_memDb['$jdb_md5']
        del tmpDb.__g_memDb['$jdb_md5']
        import hashlib
        myMd5 = hashlib.md5()
        myMd5.update(json.dumps(tmpDb.__g_memDb,indent=0, encoding='utf-8', sort_keys=True))

        #print "import str:"+ json.dumps(tmpDb.__g_memDb,indent=0, encoding='utf-8', sort_keys=True)

        if myMd5.hexdigest() != md5InFile:
            self.__debug('check md5 fail, make sure your file is created by exportToFile() function.')
            self.__debug('file md5: '+md5InFile)
            self.__debug('my md5: '+myMd5.hexdigest())
            return False

        return self.merge(tmpDb)

    @__perfDotDeco('export to file',__g_perfDot)
    def exportToFile(self, fileName=None, path='./db/'):
        '''
        导出到外部文件,可以通过importFromFile再次导入.
        :param fileName:文件名,如果为None,那么文件名默认为在init时指定的dbName.
        :param path:文件路径,默认为'./db/'
        :return:
        '''
        if not os.path.exists(path):
            os.mkdir(path)
        if fileName is None:
            fileName = self.__g_memDb['$jdb']
        fp = open(path+fileName,'w+')

        import hashlib
        if self.__g_memDb.has_key('$jdb_md5'):
            del self.__g_memDb['$jdb_md5']
        myMd5 = hashlib.md5()
        myMd5.update(json.dumps(self.__g_memDb,indent=0, encoding='utf-8', sort_keys=True))

        #print "export str:"+ json.dumps(self.__g_memDb,indent=0, encoding='utf-8', sort_keys=True)

        self.__g_memDb['$jdb_md5'] = myMd5.hexdigest()
        json.dump(self.__g_memDb,fp,indent=4, encoding='utf-8', sort_keys=True)
        fp.close()
        return True

    def ensureKey(self, collection, key):
        '''
        为colletcion指定关键字.key是一个list,支持多元组作为key.
        在同一个collection中,key保证唯一,不允许重复.
        key必须在collection没有数据之前指定.
        对于指定了key的collection,会创建一个hash索引结构.对于有hash
        索引的collection进行查找时,如果使用key进行查找,将提高查找效率.
        :param collection:collection名
        :param key:指定关键字,list类型
        :return:
        '''
        if len(key) == 0:
            return False
        coll = self.__coll(collection)
        if coll is not None: #coll已经有数据了
            if len(coll) > 0:
                return False

        if coll is None:
            self.__g_memDb['$jdb_collections'].extend([{collection:[],'$jdb_coll':collection}])
        coll = self.__coll(collection)
        coll['$jdb_key'] = key
        coll['$jdb_hash'] = [1]*self.__g_memDb['$jdb_hashSize']

        #将每个hash节点也初始化成一个list,用于处理hash冲突节点
        for i in range(0,self.__g_memDb['$jdb_hashSize']):
            coll['$jdb_hash'][i] = []
        return True

    #重载,print(jsonDb_inst)将输出数据库统计信息
    def __str__(self):
        return self.__status()






