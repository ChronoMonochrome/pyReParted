import re
from tabulate import tabulate

INVALPOS = INVALSIZE = -1

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

class Partition:
	def __init__(self, id, start = INVALPOS, size = INVALSIZE, computePos = False, removable = 0, filesystem = "", label = ""):
		assert(size != INVALSIZE)
		self.id = id
		self.size = size
		self.start = start
		self.computePos = computePos
		self.removable = removable
		self.filesystem = filesystem
		self.label = label
		
		# we don't know partition start position yet
		if not self.computePos:
			self.end = self.start + self.size

class PartitionMap:
	def __init__(self, devPath, devSize, partitions, computePos = True):
		p_count = len(partitions)
		
		partitions[0].prev = None

		if p_count > 1:
			partitions[0].next = partitions[1]

			for idx in range(1, p_count - 1):
				partitions[idx].prev = partitions[idx - 1]
				partitions[idx].next = partitions[idx + 1]
		
		partitions[p_count - 1].prev = partitions[p_count - 2]
		partitions[p_count - 1].next = None
		
		self.partitions = partitions
		
		self.computePos = computePos
		if self.computePos:
			pass
			
		self.devPath = devPath
		self.devSize = devSize
			
		self.ensureNoBogusSize()
		self.ensureNoOverlap()
		self.ensureUniqId()
		
	def createPartition(self, partition, start = INVALPOS):
		avail_space = self.getMkpartAvailSpace(start)
		p_last_part, p_last_idx = self.getMkpartPart(start)
		
		assert(partition.size <= avail_space)
		partition.id = self.getMkpartId()
		partition.start = self.getMkpartStartPos(start)
		
		p_old_next = p_last_part.next
		# WAS: p_last_part => p_last_part.next
		
		p_last_part.next = partition
		partition.prev = p_last_part
			
		partition.next = p_old_next
		if p_old_next:
			p_old_next.prev = partition
		
		# NOW: p_last_part => partition => p_old_next
		
		partition.end = partition.start + partition.size
		self.partitions.insert(p_last_idx + 1, partition)

	def removePartition(self, id):
		p, p_idx = self.getPartitionById(id)
		assert(p.removable)
		
		if p.prev:
			p.prev.next = p.next

		if p.next:
			p.next.prev = p.prev
			
		del p
		del self.partitions[p_idx]
		
	def getPartitionById(self, id):
		idx = 0
		for p in self.partitions:
			if p.id == id:
				return p, idx
			idx += 1
				
		raise(BaseException)

	def getMkpartPart(self, start = 0):
		p_curr = self.partitions[0]
		idx = 0
		
		while p_curr:
			if not p_curr.next:
				# TODO: raise something more meaningful
				return p_curr, idx
				
			if (p_curr.next.end > start and p_curr.next.start > p_curr.end):
				return p_curr, idx
				
			idx += 1
				
			p_curr = p_curr.next
			
		# should never reach here
		raise(BaseException)

	def getMkpartId(self):
		p_ids = [p.id for p in self.partitions]
		for p_id in range(1, max(p_ids) + 1):
			if not p_id in p_ids:
				return p_id
			

	def getMkpartStartPos(self, start = 0):
		p_curr = self.partitions[0]
		
		while p_curr:
			if not p_curr.next:
				# TODO: raise something more meaningful
				return p_curr.end
				
			if (p_curr.next.end > start and p_curr.next.start > p_curr.end):
				return p_curr.end
				
			p_curr = p_curr.next
			
		# should never reach here
		raise(BaseException)

	def getMkpartAvailSpace(self, pos = 0):
		p_curr, p_idx = self.getMkpartPart(pos)
		if p_curr.next:
			return p_curr.next.start - p_curr.end
		else:
			return self.devSize - p_curr.end

	def ensureUniqId(self):
		p_ids = [p.id for p in self.partitions]
		for id in p_ids:
			assert(p_ids.count(id) == 1)		

	def ensureNoOverlap(self):
		p_tmp = [[p.start, p.end] for p in self.partitions]
		p_index = 0
		#print p_tmp
		while p_tmp:
			p_curr_start, p_curr_end = p_tmp.pop(p_index)
			for p_start, p_end in p_tmp:
				#print("assert(%d >= %d or %d >= %d" % (p_curr_start, p_end, p_start, p_curr_end))
				assert(p_curr_start >= p_end or p_start >= p_curr_end)

	def ensureNoBogusSize(self):
		for p in self.partitions:
			assert(p.size > 0)
			
	def toStr(self):
		s = "Disk %s: %dkB\n\n" % (self.devPath, self.devSize)
		lines = tabulate([[p.id, p.start, p.end, p.size] for p in self.partitions], 
			headers=["Number", "Start", "End", "Size"]).split("\n")

		del lines[1] # remove header formatting
		s += "\n".join(lines)
		return s

class PartedParser:
	def __init__(self, string):
		self._data = string.split("\n")
		
	def tokenize(self):
		return [re.sub("\s+", " ", s).strip().split(" ") for s in self._data]
		
	sizeVal = lambda self, sizeStr: eval(sizeStr.replace("kB", ""))
		
	def getPartitionMap(self):
		lines = self.tokenize()
		c = 0
		for line in lines:
			if not line: continue
			if line[0] == "Disk": break
			c += 1
		
		devPath, devSize = line[1].replace(":", ""), self.sizeVal(line[2])
			
		for line in lines[c:]:
			c += 1
			if not line: continue
			if line[0] == "Number": break
			
		partitions = []
		for line in lines[c:]:
			if not line: break
			id, start, end, size = eval(line[0]), self.sizeVal(line[1]), self.sizeVal(line[2]), self.sizeVal(line[3])
			partitions.append(Partition(id, start = start, size = size, removable = True))
		return PartitionMap(devPath, devSize, partitions)
		
def repartDev(partedParser, startPos, partIdsToRemove, partsSizesToCreate):
	pp = partedParser
	pm = pp.getPartitionMap()
	p_ids = [p.id for p in pm.partitions]
	
	for id in partIdsToRemove:
		if id in p_ids:
			pm.removePartition(id)
		else:
			print("warning: skipping non-existing partition %d" % id)

	for size in partsSizesToCreate:
		new_id = pm.getMkpartId()
		p = Partition(id = new_id, start = startPos, size = size)
		pm.createPartition(p, start = p.start)
		startPos += size
		
	return pm