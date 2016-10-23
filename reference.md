# JsonDB
jsonDB是一个基于JSON格式的内存数据库.它具有以下特点:
>+ 轻量级. 无守护进程,无需任何额外的安装和配置,你只需要```import jsonDb```即可使用,非常方便.
>+ NOSQL. 类似于mongoDb的非关系型数据库.
>+ 内存数据库. 所有数据基于内存进行操作和访问,性能相对较高.目前版本的性能测试数据请
参考reference文档.
>+ 任意迁移. 数据库可以完整导出为外部文件,并且可以从外部文件导入.基于此,数据库可以
进行任意的迁移,而无需做任何修改.
>+ 灵活的数据类型. 一个数据集合(collection)中的数据,并不需要相同的格式.比如以下几种数据
> 可以同时存在于一个collection中:
> ```{'key1':1},{'key2':'value','pic':'value'},{'key3':'value'}```

## 概念说明:
>+ db: 即数据库. 创建一个jsonDb类的实例,即是创建了一个数据库.可以指定dbname和hash的长度.
>+ collection: 数据集合(表). 一个collection可以理解为数据库中的一个表. collection不需要
  单独创建,当insert第一条数据,或者ensureKey时,系统会自动创建.
>+ data: 数据. collection中的一条数据,或者是一个数据的list. data必须是dict字典类型,是一个
key-value键值对.

## 关键词说明:
以下关键词属于系统保留,不能作为任何字典dict的key名.
```
$lt 
$lte 
$gt 
$gte 
$ne 
$or 
$or[0-9] 
$jdb 
$jdb_collections 
$jdb_key 
$jdb_hash 
$jdb_coll 
$jdb_hashSize 
$jdb_md5
```
## 安装
1. 从源码安装,首先从github下载源码,[jsonDb源码下载地址](https://github.com/hujiang001/jsonDB)
```
python setup.py install
```
2. pypi直接安装,注意本项目后续会上传到pypi,目前仅支持源码安装.
```
pip install jsonDb
```

## Filter条件过滤器
很多操作会使用到Filter条件过滤器.比如,删除数据\更新数据\查询数据等.通过过滤器,我们可以指定更新一组满足一定条件的数据.
jsonDb提供了相对丰富和灵活的过滤器. 过滤器一般在方法的参数中使用filter来指定.

filter是一个dict,它包括key,value,逻辑表达式,条件表达式 几个部分.

```
filter={'逻辑表达式':{key:{'条件表达式':value}}}
```

逻辑表达式: 支持两种逻辑

1. 逻辑或: ```'$or'``` ```'$or1'``` ```'$or2'```...,,如果存在多个逻辑或,需要使用$or[0-9],例如:
```
filter={'$or':{'key1':value1, 'key2':value2,...}, '$or1':{'key1':value1, 'key2':value2,...}, ...}
```
2. 逻辑与: 没有特殊的关键字,没有使用逻辑或关键字的{}内的key之间就是逻辑与的关系,例如:
```
filter={'key1':value1, 'key2':value2,...}
```

条件表达式: 条件表达式是用来表示key和value之间的关系

+ 等于	    ```{<key>:<value>}```
+ 小于     	```{<key>:{$lt:<value>}}```
+ 小于或等于	```{<key>:{$lte:<value>}}```
+ 大于	        ```{<key>:{$gt:<value>}}```
+ 大于或等于	```{<key>:{$gte:<value>}}```
+ 不等于    	```{<key>:{$ne:<value>}}```


Filter支持任意嵌套,这样使用起来会非常灵活.如下:

```
filter={'$or':{'key1':value1, '$or':{'key1':value1, '$or1':{'key1':value1, 'key2':value2,...},...},...}, 
        '$or1':{'key1':value1, 'key2':value2,...}, ...}
```


## 功能说明:
### 创建数据库

实例化一个JSONDB类实例,即创建一个数据库.我们重载了```__str__```方法,所以可以通过```print```直接查看数据库的统计信息.
```
>>> from jsonDb.database import JSONDB
>>> myDb = JSONDB('USER_DB')
>>> print myDb

------ jdb statics ------
db_name: USER_DB
mem_collection: 0 bytes
mem_hash: 0 bytes
collection_num: 0
**** collection statics **** 
```
### 删除数据库
jsonDB是内存数据库,一个数据库本质上就是一个类实例.所以数据库随类实例进行删除和释放.你可以通过```del```方法删除这个类实例,
当然也可以让python自己回收.

### 插入数据
插入一条数据,则对应的collection自动创建.可以插入一条或多条数据,必须通过```list```格式组织.单条数据必须是```dict```格式.

```
>>> myDb.insert('COL_CUSTOMERS',[{'id':1, 'name':'Jeffery', 'sex':'male', 'age':18, 'birth':'1990-01-03'}])
True
>>> print myDb

------ jdb statics ------
db_name: USER_DB
mem_collection: 104 bytes
mem_hash: 0 bytes
collection_num: 1
**** collection statics **** 
 name: COL_CUSTOMERS
 data_num: 0
 key: []
 index: False
 data_mem: 104 bytes
 hash_mem: 0 bytes

>>> 
```

可以通过```find()```查看插入结果,为了显示格式更加便于阅读,JSONDB提供了静态格式化打印方法```rprint()```:

```
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS'),indent=4)
[
    {
        "name": "Jeffery", 
        "age": 18, 
        "id": 1, 
        "birth": "1990-01-03", 
        "sex": "male"
    }
]
>>> 
```

也可以同时插入多条数据

```
>>> dataList = [{'id':2, 'name':'Jack', 'sex':'male', 'age':29, 'birth':'1990-01-03'},
...             {'id':3, 'name':'Tom', 'age':18, 'birth':'1991-01-03'},
...             {'id':4, 'name':'Wang', 'sex':'male', 'age':40, 'job':'software engineer'}]
>>> myDb.insert('COL_CUSTOMERS',dataList)
True
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS',filter={'id':{'$gte':2}}),indent=4)
[
    {
        "name": "Jack", 
        "age": 29, 
        "id": 2, 
        "birth": "1990-01-03", 
        "sex": "male"
    }, 
    {
        "age": 18, 
        "id": 3, 
        "birth": "1991-01-03", 
        "name": "Tom"
    }, 
    {
        "id": 4, 
        "job": "software engineer", 
        "age": 40, 
        "name": "Wang", 
        "sex": "male"
    }
]
>>> 

```

上面使用了```find()```方法的条件查询,只查询了```'id'```大于等于2的数据.同时,每条data之间的格式不需要一致.

### 删除数据
删除一条指定的数据:
```
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS',filter={'id':1}),indent=4)
[
    {
        "name": "Jeffery", 
        "age": 18, 
        "id": 1, 
        "birth": "1990-01-03", 
        "sex": "male"
    }
]
>>> myDb.delete('COL_CUSTOMERS',filter={'id':1})
True
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS',filter={'id':1}),indent=4)
[]
>>> 

```
同样,我们可以通过filter过滤器来条件删除多条数据,比如我们要删除所有```'age'```大于10并且小于30的记录:
```
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS'),indent=4)
[
    {
        "name": "Jack", 
        "age": 29, 
        "id": 2, 
        "birth": "1990-01-03", 
        "sex": "male"
    }, 
    {
        "age": 18, 
        "id": 3, 
        "birth": "1991-01-03", 
        "name": "Tom"
    }, 
    {
        "id": 4, 
        "job": "software engineer", 
        "age": 40, 
        "name": "Wang", 
        "sex": "male"
    }, 
    {
        "name": "Jeffery", 
        "age": 18, 
        "id": 1, 
        "birth": "1990-01-03", 
        "sex": "male"
    }
]
>>> myDb.delete('COL_CUSTOMERS',filter={'age':{'$gt':10,'$lt':30}})
True
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS'),indent=4)
[
    {
        "id": 4, 
        "job": "software engineer", 
        "age": 40, 
        "name": "Wang", 
        "sex": "male"
    }
]
>>> 

```

### 数据更新

```
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS',filter={'name':'Wang'}),indent=4)
[
    {
        "id": 4, 
        "job": "software engineer", 
        "age": 40, 
        "name": "Wang", 
        "sex": "male"
    }
]
>>> myDb.update('COL_CUSTOMERS',set={'job':'doctor'},filter={'name':'Wang'})
True
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS',filter={'name':'Wang'}),indent=4)
[
    {
        "id": 4, 
        "job": "doctor", 
        "age": 40, 
        "name": "Wang", 
        "sex": "male"
    }
]
>>> 
```

### 数据查询
数据查询可以使用Filter过滤器来实现丰富的查找功能.

```
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS'),indent=4)
[
    {
        "name": "Jeffery", 
        "age": 18, 
        "id": 1, 
        "birth": "1990-01-03", 
        "sex": "male"
    }, 
    {
        "name": "Jack", 
        "age": 29, 
        "id": 2, 
        "birth": "1990-01-03", 
        "sex": "male"
    }, 
    {
        "age": 18, 
        "id": 3, 
        "birth": "1991-01-03", 
        "name": "Tom"
    }, 
    {
        "id": 4, 
        "job": "software engineer", 
        "age": 40, 
        "name": "Wang", 
        "sex": "male"
    }
]
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS',filter={'$or':{'age':{'$gt':20},'id':{'$gte':3}}}),indent=4)
[
    {
        "name": "Jack", 
        "age": 29, 
        "id": 2, 
        "birth": "1990-01-03", 
        "sex": "male"
    }, 
    {
        "age": 18, 
        "id": 3, 
        "birth": "1991-01-03", 
        "name": "Tom"
    }, 
    {
        "id": 4, 
        "job": "software engineer", 
        "age": 40, 
        "name": "Wang", 
        "sex": "male"
    }
]

```
如果不指定collection,那么将在整个数据库中查找.目前暂不支持指定多个collection查找.

可以通过```limit```参数来限制返回数据的条数,默认为0,也就是返回所有.如下:
```
>>> JSONDB.rprint(myDb.find('COL_CUSTOMERS',filter={'$or':{'age':{'$gt':20},'id':{'$gte':3}}},limit=2),indent=4)
[
    {
        "name": "Jack", 
        "age": 29, 
        "id": 2, 
        "birth": "1990-01-03", 
        "sex": "male"
    }, 
    {
        "age": 18, 
        "id": 3, 
        "birth": "1991-01-03", 
        "name": "Tom"
    }
]

```
目前版本暂不支持排序和指定返回字段集,后续版本会陆续支持.

### 指定Key值
可以通过```ensureKey()```给collection指定key值,这个key值是一个list,可以是一个多元组key.
指定了key值的collection将会保证key值的唯一性,也就是说collection中的数据key值不会重复.
同时,指定了key值过后,将会为该collection自动创建一个hash表,建立索引.在```find()```中,
如果```filter```是严格指定的key值,那么将自动进行hash查找,查找效率比普通查找高很多.hash表
的大小在创建数据库时可以指定```hashSize```,默认是1000.
需要注意的是,我们只能当collection里面没有数据时才能调用```ensureKey()```,一旦有插入数据后再指定Key值则失败.


### 数据库合并
通过```merge()```将一个数据库合并到另外一个数据库里面.合并中如果遇到数据冲突(比如key值冲突),则合并失败.
```
>>> mergeDb = JSONDB('mergeDb')
>>> mergeDb.insert('COL1',[{'id':1,'name':'Wang'}])
True
>>> mergeToDb = JSONDB('mergeToDb')
>>> mergeToDb.insert('COL1',[{'id':2,'name':'LI'}])
True
>>> mergeToDb.insert('COL2',[{'idX':1,'nameX':'Lee'}])
True
>>> mergeDb.merge(mergeToDb)
True
>>> JSONDB.rprint(mergeDb.find(),indent=4)
[
    {
        "id": 1, 
        "name": "Wang"
    }, 
    {
        "id": 2, 
        "name": "LI"
    },
    {
        "idX": 1, 
        "nameX": "Lee"
    }
]
>>> 

```

### 导出数据库到外部文件
jsonDB是内存数据库,为了数据的持久存储,我们支持将内存数据库导出到外部磁盘文件中.
```
>>> mergeDb.exportToFile()
True
```
默认将文件导出到```./db/```目录下,db文件以数据库的名字命名. 上例中将导出到```./db/mergeDb```.

导出的过程是比较耗时的,目前我们不支持实时导出,需要使用者适配这部分功能.

### 从外部文件导入数据库
支持从外部文件中导入数据到一个JSONDB类实例中.
```
>>> importDb = JSONDB('DB_IMPORT')
>>> importDb.importFromFile(fileName='mergeDb')
True
```
导入的数据库文件,必须是通过```exportToFile()```导出生成的,否则导入操作可能会失败.
为了防止外部文件数据被篡改,我们使用了```MD5```进行数据完整性校验,所以不要修改导出的数据文件.

### 一些维测手段
#### 调试打印开关
```
>>> myDb.debugSwitch(1)
```

#### 格式化输出

参数```indent```表示缩进的字符个数

```
>>> JSONDB.rprint(mergeDb.find(),indent=4)
[
    {
        "id": 1, 
        "name": "Wang"
    }, 
    {
        "idX": 1, 
        "nameX": "Lee"
    }
]
```
#### 数据库统计信息
使用```print```方法即可打印出数据库的详细统计信息.
```
>>> print myDb

------ jdb statics ------
db_name: USER_DB
mem_collection: 104 bytes
mem_hash: 0 bytes
collection_num: 1
**** collection statics **** 
 name: COL_CUSTOMERS
 data_num: 0
 key: []
 index: False
 data_mem: 104 bytes
 hash_mem: 0 bytes

>>> 
```

- db_name - 数据库名
- mem_collection - collection消耗的总内存
- mem_hash - hash表消耗的总内存
- collection_num - collection个数
- collection statics - 分别显示每个collection的信息
   * name - collection名
   * data_num - data总条数
   * key - 指定的关键字列表
   * index - 是否建立了索引
   * data_mem - 数据占用内存
   * hash_mem - hash表占用内存

#### 关键过程性能打点

方法```perfDotStart()```和```perfDotEnd()```配对使用,提供对关键流程的耗时统计,毫秒级.

```
myDb.perfDotStart()
for i in range(1,1000):
    myDb.insert('COL_CUSTOMERS',[{'id':i, 'name':'Jeffery', 'sex':'male', 'age':18, 'birth':'1990-01-03'}])

myDb.find('COL_CUSTOMERS',filter={'id':500})
myDb.perfDotEnd()
```

输出结果:
```
------ perf dot statics ------
[insert]spend time: 0.005295753479
[find]spend time: 0.014662027359
```

注意,这里统计的是某个关键流程的总耗时.比如,期间进行了多次```insert()```操作,那么insert的耗时统计是所有这些的总和.

## 关于性能
jsonDb是基于内存存储,所以整体性能足以满足一些小型的数据库应用.

作者用来测试的PC性能:
```
mac air book
处理器  1.4 GHz Intel Core i5
内存  4 GB 1600 MHz DDR3
操作系统 OS X 10.9.5 (13F1603)
```

测试十万条数据的插入\删除\查询操作:
```
from jsonDb.database import  JSONDB

myDb = JSONDB('USER_DB')

myDb.perfDotStart()
for i in range(0,100000):
    myDb.insert('COL_CUSTOMERS',[{'id':i, 'name':'Jeffery', 'sex':'male', 'age':18, 'birth':'1990-01-03'}])
myDb.perfDotEnd()

myDb.perfDotStart()
myDb.find('COL_CUSTOMERS',filter={'id':500})
myDb.perfDotEnd()

myDb.perfDotStart()
myDb.delete('COL_CUSTOMERS',filter={'id':10000})
myDb.perfDotEnd()
```
打点结果如下:
```
------ perf dot statics ------
[insert]spend time: 0.450565576553

------ perf dot statics ------
[find]spend time: 1.62476110458

------ perf dot statics ------
[find]spend time: 1.59516096115
[delete]spend time: 1.59673404694
```

指定了key值过后,会建立索引,所以会大大提高查找性能,但是插入性能会有一定下降.

```
from jsonDb.database import  JSONDB

myDb = JSONDB('USER_DB')

# 指定key值
myDb.ensureKey('COL_CUSTOMERS',['id'])

myDb.perfDotStart()
for i in range(0,100000):
    myDb.insert('COL_CUSTOMERS',[{'id':i, 'name':'Jeffery', 'sex':'male', 'age':18, 'birth':'1990-01-03'}])
myDb.perfDotEnd()

myDb.perfDotStart()
myDb.find('COL_CUSTOMERS',filter={'id':500})
myDb.perfDotEnd()

myDb.perfDotStart()
myDb.delete('COL_CUSTOMERS',filter={'id':10000})
myDb.perfDotEnd()
```
打点结果如下:
```
------ perf dot statics ------
[insert]spend time: 6.04253554344

------ perf dot statics ------
[find]spend time: 9.91821289062e-05

------ perf dot statics ------
[find]spend time: 6.50882720947e-05
[delete]spend time: 0.00128698348999
```

## LICENCE
遵循 The MIT License (MIT),你可以不受约束地使用该项目代码和生成件.

## 反馈和交流
mail:hujiang001@gmail.com
https://github.com/hujiang001/jsonDB


