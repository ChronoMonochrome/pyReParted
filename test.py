from pyreparted import *

codinaPart2Label = {
	3: "SYSTEM",
	4: "CACHEFS",
	5: "DATAFS",
	8: "UMS",
	9: "SYSTEM2",
	11: "DATAFS2"
}

codinaPartitions = [
	Partition(id = 3, label = "SYSTEM", filesystem = "ext4", removable = True),
	Partition(id = 4, label = "CACHEFS", filesystem = "ext4", removable = True),
	Partition(id = 5, label = "DATAFS", filesystem = "ext4", removable = True),
	Partition(id = 8, label = "UMS", filesystem = "fat32", removable = True),
	Partition(id = 9, label = "SYSTEM2", filesystem = "ext4", removable = True),
	Partition(id = 11, label = "DATAFS2", filesystem = "ext4", removable = True)
]

def test():
	p10 = Partition(10, start = 524, size = 1049, removable = False, label = "PIT")
	p6 = Partition(6, start = 1573, size = 1573, removable = False, label = "CSPSA FS")
	p7 = Partition(7, start = 4194, size = 10486, removable = False, filesystem = "ext4", label = "EFS")
	p2 = Partition(2, start = 14680, size = 16777, removable = False, filesystem = "ext4", label = "Modem FS")
	p14 = Partition(14, start = 32506, size = 2097, removable = False, label = "SBL")
	p16 = Partition(16, start = 34603, size = 2097, removable = False, label = "SBL_2")
	p1 = Partition(1, start = 36700, size = 16777, removable = False, label = "PARAM")
	p12 = Partition(12, start = 53477, size = 2097, removable = False, label = "IPL Modem")
	p13 = Partition(13, start = 55575, size = 16777, removable = False, label = "Modem")
	p15 = Partition(15, start = 72352, size = 16777, removable = False, label = "Kernel")
	p17 = Partition(17, start = 89129, size = 16777, removable = False, label = "Kernel2")
	p3 = Partition(3, start = 105906, size = 820000, removable = True, filesystem = "ext4", label = "System")
	p4 = Partition(4, start = 925906, size = 15000, removable = True, filesystem = "ext4", label = "Cache FS")
	p5 = Partition(5, start = 940906, size = 1031465, removable = True, filesystem = "ext4", label = "Data FS")
	p8 = Partition(8, start = 1972371, size = 100000, removable = True, filesystem = "fat32", label = "UMS")
	p9 = Partition(9, start = 2072371, size = 900000, removable = True, filesystem = "ext4", label = "System 2")
	p11 = Partition(11, start = 2972371, size = 987035, removable = True, filesystem = "ext4", label = "Data 2")
	
	return [p10, p6, p7, p2, p14, p16, p1, p12, p13, p15, p17, p3, p4, p5, p8, p9, p11]

partedOutput = """Model:  (file)
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

pp = PartedParser(partedOutput)
pm = pp.getPartitionMap()

codinaPartitions = getPartitions2(partitions = codinaPartitions, 
        partSizes = [820000000, 139696000, 1902931000, 989080000, 1324000], startPos = 105906176)

ps = PartedScript(pm)
ps.repartDev(partIdsToRemove = [3,4,5,8,9], partitions = codinaPartitions)

script = ps.generate(unitTest = True)

print script

