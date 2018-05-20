import sys
from pyreparted import *

pp = PartedParser(open(sys.argv[1], "r").read())
pm = pp.getPartitionMap()
codinaPartitions = [
	Partition(id = 3, label = "SYSTEM", size = 1020000256, filesystem = "ext4", removable = True),
	Partition(id = 4, label = "CACHEFS", size = 15000064, filesystem = "ext4", removable = True),
	Partition(id = 5, label = "DATAFS", size = 1031464960, filesystem = "ext4", removable = True),
	Partition(id = 8, label = "UMS", size = 99999744, filesystem = "fat32", removable = True),
	Partition(id = 9, label = "SYSTEM2", size = 900000256, filesystem = "ext4", removable = True),
	Partition(id = 11, label = "DATAFS2", size = 787034624, filesystem = "ext4", removable = True)
]

codinaPartitions = getPartitions2(partitions = codinaPartitions, startPos = 105906176)

ps = PartedScript(pm)
ps.repartDev(partIdsToRemove = [3, 4, 5, 8, 9, 11], partitions = codinaPartitions)
script = ps.generate(unitTest = False)
print(script)
