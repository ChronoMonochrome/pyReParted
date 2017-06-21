# pyReParted
A python module to simulate a device repartition

# Usage:

We first need to get `parted <device> unit b print` output, to parse the existing device partition layout:
```python
>>> partedOutput = """Model:  (file)
Disk /home/chrono/root/EMMC.img: 3959422976B
Sector size (logical/physical): 512B/512B
Partition Table: gpt
Disk Flags:

Number  Start        End          Size         File system  Name     Flags
10      524288B      1572863B     1048576B                  primary
 6      1572864B     3145727B     1572864B                  primary
 7      4194304B     14680063B    10485760B                 primary
 2      14680064B    31457279B    16777216B                 primary
14      32505856B    34603007B    2097152B                  primary
16      34603008B    36700159B    2097152B                  primary
 1      36700160B    53477375B    16777216B                 primary
12      53477376B    55574527B    2097152B                  primary
13      55574528B    72351743B    16777216B                 primary
15      72351744B    89128959B    16777216B                 primary
17      89128960B    105906175B   16777216B                 primary
 3      105906176B   756023295B   650117120B                SYSTEM
 4      756023296B   766509055B   10485760B                 CACHEFS
 5      766509056B   3844079615B  3077570560B               DATAFS
 8      3844079616B  3938451455B  94371840B                 UMS
 9      3938451456B  3959357439B  20905984B                 SYSTEM2"""
 ```
 
Parse the string above:
```python
>>> ps = PartedParser(partedOutput)
```
Retrieve the partition layout:
```python
>>> pm = pp.getPartitionMap()
``` 
Create some Partition objects with id, label and file system assigned:
```python 
>>> codinaPartitions = [
	Partition(id = 3, label = "SYSTEM", filesystem = "ext4", removable = True),
	Partition(id = 4, label = "CACHEFS", filesystem = "ext4", removable = True),
	Partition(id = 5, label = "DATAFS", filesystem = "ext4", removable = True),
	Partition(id = 8, label = "UMS", filesystem = "fat32", removable = True),
	Partition(id = 9, label = "SYSTEM2", filesystem = "ext4", removable = True),
	Partition(id = 11, label = "DATAFS2", filesystem = "ext4", removable = True)
]
```
Now assign size, start and end positions to them:
```python
>>> codinaPartitions = getPartitions2(partitions = codinaPartitions, 
        partSizes = [820000000, 139696000, 1902931000, 989080000, 1324000], startPos = 105906176)
```        
This will assign size to first five given partitions (this depends on the length of partSizes list parameter).
The start position of first partition passed to this function by parameter startPos.
Other partitions will be located right after each other. Note that only first five Partition objects will be returned by getPartitions2 function.

Now, virtually apply this repartition:
```python
>>> ps = PartedScript(pm)
>>> ps.repartDev(partIdsToRemove = [3,4,5,8,9], partitions = codinaPartitions)
```

This will remove partitions with IDs 3, 4, 5, 8 and 9 and create partitions passed by `partitions` parameter.
If some error will occur, e.g. partitions can't fit on this device, an exception will be arisen.

Finally, produce the repartition script:
```python
>>> script = ps.generate(unitTest = False)
>>> print script
```

Setting unitTest parameter to True will result in that the script produced will not try to unmount partitions. 
It can be useful when testing the script on a file image, before actually applying the layout to the real device.

```
#!/sbin/sh
#-------------------------------------------------#
#                 CWM ReParted                    #
#-------------------------------------------------#

MMC=/home/chrono/root/EMMC.img
UMS=8
SYSTEM2=9
SYSTEM=3
CACHEFS=4
DATAFS=5
p=p

# umount partitions
umount  $MMC$p$UMS
umount  $MMC$p$SYSTEM2
umount  $MMC$p$SYSTEM
umount  $MMC$p$CACHEFS
umount  $MMC$p$DATAFS

# remove partitions
parted $MMC rm $SYSTEM
parted $MMC rm $CACHEFS
parted $MMC rm $DATAFS
parted $MMC rm $UMS
parted $MMC rm $SYSTEM2

# re-create partitions
# SYSTEM - (103424 - 904192 kB), size 800768 kB
parted $MMC unit b mkpart primary ext4 105906176 925892607 

# CACHEFS - (904192 - 1040384 kB), size 136192 kB
parted $MMC unit b mkpart primary ext4 925892608 1065353215 

# DATAFS - (1040384 - 2897920 kB), size 1857536 kB
parted $MMC unit b mkpart primary ext4 1065353216 2967470079 

# UMS - (2897920 - 3863552 kB), size 965632 kB
parted $MMC unit b mkpart primary fat32 2967470080 3956277247 

# SYSTEM2 - (3863552 - 3864576 kB), size 1024 kB
parted $MMC unit b mkpart primary ext4 3956277248 3957325823 


# assign labels
parted $MMC name $UMS UMS
parted $MMC name $SYSTEM2 SYSTEM2
parted $MMC name $SYSTEM SYSTEM
parted $MMC name $CACHEFS CACHEFS
parted $MMC name $DATAFS DATAFS```


