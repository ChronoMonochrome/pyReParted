import re
from tabulate import tabulate

INVALPOS = INVALSIZE = INVALID = -1
SZ_1K = 1024
SZ_1M = 1024 ** 2

def setRemovable(partitionMap, partitions):
	p_ids = [p.id for p in partitionMap.partitions]
	for p in partitions:
		if p.id in p_ids:
			partitionMap.getPartitionById(p.id).setRemovable(p.removable)
	return partitionMap

def getPartitions(part2Label, partSizes, startPos):
	partitions = []
	for l, s in zip(part2Label.values(), partSizes):
		p = Partition(start = startPos, label = l, size = s)
		partitions.append(p)
		startPos += s
	return partitions

def getPartitions2(partitions, partSizes, startPos):
	res = []
	for p, size in zip(partitions, partSizes):
		p.size = size
		p.start = startPos
		p.end = startPos + p.size
		startPos = p.end
		p.alignSize()
		res.append(p)
	return res
	
class AvailableSpaceException(Exception):
	pass
	
class UnsupportedFSException(Exception):
	pass

class Partition:
	def __init__(self, id = INVALID, start = INVALPOS, size = INVALSIZE, align = SZ_1M,
				removable = False, filesystem = "", label = "", umountFlags = ""):
				
		self.id = id
		self.start = start
		self.removable = removable
		self.filesystem = filesystem
		self.label = label
		self.umountFlags = umountFlags
		if size != INVALSIZE and align:
			# round down
			size //= align
			size *= align
			
		self.size = size
		self.end = self.start + self.size
			
	def assignLabel(self, label):
		self.label = label
		
	def isRemovable(self):
		return self.removable
		
	def setRemovable(self, removable):
		self.removable = removable
		
	def alignSize(self, align = SZ_1M):
		if self.size == INVALSIZE:
			raise ValueError("cannot align partition size without the correct size set")
	
		self.size //= align
		self.size *= align

class PartitionMap:
	supportedFs =  ["ext2", "ext3", "ext4",
				"fat16", "fat32", "hfs", "jfs", 
				"linux-swap", "ntfs", "reiserfs", "ufs", "xfs"]
	
	def __init__(self, devPath, devSize, partitions):
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
					
		self.devPath = devPath
		self.devSize = devSize
			
		self.ensureNoBogusSize()
		self.ensureNoOverlap()
		self.ensureUniqId()
		self.ensureNoBogusId()
		
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
		p = self.getPartitionById(id)
		assert(p.removable)
		
		# p.prev => p => p.next
		
		if p.prev:
			p.prev.next = p.next

		if p.next:
			p.next.prev = p.prev
			
		# p.prev => p.next
			
		self.delPartitionById(id)
		
	def getPartitionById(self, id):
		for p in self.partitions:
			if p.id == id:
				return p
				
		raise(BaseException)
		
	def delPartitionById(self, id):
		idx = 0
		for p in self.partitions:
			if p.id == id:
				del self.partitions[idx]
				return
			idx += 1
				
		raise(BaseException)

	def getMkpartPart(self, start = 0):
		p_curr = self.partitions[0]
		idx = 0
		
		while p_curr:
			if not p_curr.next:
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
				return p_curr.end
				
			if (p_curr.next.end > start and p_curr.next.start > p_curr.end):
				return p_curr.end
				
			p_curr = p_curr.next
			
		# should never reach here
		assert(False)

	def getMkpartAvailSpace(self, pos = 0):
		p_curr, p_idx = self.getMkpartPart(pos)
		if p_curr.next:
			return p_curr.next.start - p_curr.end
		else:
			# several latest device sectors are occupied by GPT backup header
			return (self.devSize - 64 * SZ_1K) - p_curr.end

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
			
	def ensureNoBogusId(self):
		for p in self.partitions:
			assert(p.id > 0)
			
	def toStr(self):
		s = "Disk %s: %dkB\n\n" % (self.devPath, self.devSize)
		lines = tabulate([[p.id, p.start, p.end, p.size, p.filesystem, p.label] for p in self.partitions], 
			headers=["Number", "Start", "End", "Size", "File system", "Name"]).split("\n")

		del lines[1] # remove header formatting
		s += "\n".join(lines)
		return s

class PartedParser:
	def __init__(self, string):
		self._data = string.split("\n")
		
	def tokenize(self, singleSpaceToDelimiter):
		# replace every single space between words by delimiter
		lines = [re.sub(r'([^\s])\s([^\s])', r'\1%s\2' % \
				(singleSpaceToDelimiter), s) for s in self._data]
		# replace multiple spaces by just one space and tokenize every line
		return [re.sub("\s+", " ", s).strip().split(" ") for s in lines]
		
	sizeVal = lambda self, sizeStr: eval(sizeStr.replace("B", ""))
		
	def getPartitionMap(self):
		singleSpaceToDelimiter = "%20"
		lines = self.tokenize(singleSpaceToDelimiter)
		c = 0
		for line in lines:
			if not line: continue
			if line[0].startswith("Disk"): break
			c += 1
		
		line = line[0].split(singleSpaceToDelimiter)
		devPath, devSize = line[1].replace(":", ""), self.sizeVal(line[2])
			
		for line in lines[c:]:
			c += 1
			if not line: continue
			if line[0].startswith("Number"): break
			
		partitions = []
		for line in lines[c:]:
			if not line: break
			id, start, end, size = eval(line[0]), self.sizeVal(line[1]), \
							self.sizeVal(line[2]), self.sizeVal(line[3])
			fs = ""
			label = ""
			if len(line) == 5:
				if line[4] in PartitionMap.supportedFs:
					fs = line[4]
				else:
					label = line[4]
			elif len(line) == 6:
				fs, label = line[4], line[5]

			label = label.replace(singleSpaceToDelimiter, " ")
			partitions.append(Partition(id, start = start, size = size, removable = True,
						filesystem = fs, label = label))
		return PartitionMap(devPath, devSize, partitions)
		
class PartedScript:
	def __init__(self, partitionMap):
		self.partitionMap = partitionMap

	
	def repartDev(self, partIdsToRemove, partitions):
		self.partIdsToRemove = partIdsToRemove
		self.partitions = partitions
		pm = self.partitionMap
		
		p_ids = []
		
		for p in pm.partitions:
			if p.filesystem and not p.filesystem in PartitionMap.supportedFs:
				raise UnsupportedFSException("file system %s is not supported by parted" % p.filesystem)
			p_ids.append(p.id)

		for p_id in self.partIdsToRemove:
			if p_id in p_ids:
				assert(self.partitionMap.getPartitionById(p_id).isRemovable())
			else:
				print("PartedScript: warning: skipping partition %d" % p_id)

	
		for id in self.partIdsToRemove:
			if id in p_ids:
				pm.removePartition(id)
			else:
				print("warning: skipping non-existing partition %d" % id)

		self.part2Label = {}
		self.umountFlags = {}
		self.partIdsToRecreate = []
		for p in self.partitions:
			p.id = pm.getMkpartId()
			self.part2Label[p.id] = p.label
			self.umountFlags[p.id] = p.umountFlags
			pm.createPartition(p, start = p.start)
			self.partIdsToRecreate.append(p.id)
		
		return pm
		
	def generate(self, unitTest = False, ignoreAlignment = False):
		s =  "#!/sbin/sh\n"
		s += "#-------------------------------------------------#\n"
		s += "#                 CWM ReParted                    #\n" 
		s += "#-------------------------------------------------#\n\n"
		
		s += "MMC=%s\n"	% (self.partitionMap.devPath)

		for p_id, label in self.part2Label.items():
			s += "%s=%d\n" % (label, p_id)
			
		s += "p=p\n\n"
		
		if not unitTest:
			s += "# umount partitions\n"
			for p_id, label in self.part2Label.items():
				umountFlags = ""
				if p_id in self.umountFlags.keys():
					umountFlags = self.umountFlags[p_id]

				s += "umount %s $MMC$p$%s\n" % (umountFlags, label)
			
		s += "\n# remove partitions\n"

		for p_id in self.partIdsToRemove:
			label = self.part2Label[p_id]
			s += "parted $MMC rm $%s\n" % (label)
			
		s += "\n# re-create partitions\n"
		for p_id in self.partIdsToRecreate:
			p = self.partitionMap.getPartitionById(p_id)
			s += "# %s - (%d - %d kB), size %d kB\n" % \
				(self.part2Label[p_id], p.start / 1024, p.end / 1024, p.size / 1024)
			s += "parted $MMC unit b mkpart primary %s %d %d %s\n\n" \
					% ("" if not p.filesystem else p.filesystem, p.start, \
					p.end - 1, ("i 1>/dev/null 2>1" if ignoreAlignment else ""))
	
		s += "\n# assign labels\n"
		for p_id, label in self.part2Label.items():
			s += "parted $MMC name $%s %s\n" % (label, label)
			
		return s



