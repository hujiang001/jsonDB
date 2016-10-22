# JsonDB


jsonDB is a light and NoSQL memory-database based on JSON format.
jsonDB是一个基于JSON格式的内存数据库.

### version

1.0.0 - release

### dependence

python 2.7

### 特点:
>1、轻量级. 无守护进程,无需任何额外的安装和配置,你只需要import jsonDb即可使用,非常方便.


>2、NOSQL. 类似于mongoDb的非关系型数据库.


>3、内存数据库. 所有数据基于内存进行操作和访问,性能相对较高.目前版本的性能测试数据请参考reference文档.


>4、任意迁移. 数据库可以完整导出为外部文件,并且可以从外部文件导入.基于此,数据库可以进行任意的迁移,而无需做任何修改.


>5、灵活的数据类型. 一个数据集合(collection)中的数据,并不需要相同的格式.比如以下几种数据可以同时存在于一个collection中:{'key1':1},{'key2':'value','pic':'value'},{'key3':'value'}


### 当前支持的功能:

* 数据插入

* 数据删除

* 数据更新

* 数据查询(支持丰富的条件查询)

* 指定key值(支持key值hash查找,提高效率)

* 数据库合并

* 导出数据库到外部文件

* 从外部文件导入数据库

* 关键过程性能打点(毫秒级耗时统计)

* 数据库统计显示(包括数据规模\占用内存等)

* 格式化打印



### API文档和使用实例

去往    [wiki===========>](http://链接网址)


### install

```python setup.py install```


### LICENCE
The MIT License (MIT)


