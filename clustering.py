import align

#Currently we just throw out peaks that the alignment algorithm
#doesn't align (returns 0 instead)
outlierThreshold = 0



#In case the datatype changes, or we want to
#remember the cluster of the peak by storing it in the peak
def group (peak, peakIndex, meanIndex, clusters, assignments):
	clusters[meanIndex] += [peak]
	assignments[peakIndex] = meanIndex

#Generates blank prototypes. Shouldn't be affected by paring
def initializePrototypes(means):
	prototypes = []
	for m in range(len(means)):
		#The prototypical mean, generated during allocation
		prototype = []
		(mean,targetLength) = means[m]
		for n in range(len(mean)):
			#for now, to try and prevent null means. (Laplace's smoothing)
			# prototype += [[0.0,0.0,0.0,0.0]]
			prototype += [[0.25,0.25,0.25,0.25]]
		prototypes += [prototype]
	return prototypes

#Counts the character's contribution to the mean 
# at that position in the sequence and mean
def count (character, probArray):
	if character == 'A':
		probArray[0] += 1
	elif character == 'T':
		probArray[1] += 1
	elif character == 'G':
		probArray[2] += 1
	elif character == 'C':
		probArray[3] += 1
	else:
		print "Incorrect string in peaks (recentering), implement error handling"
	return

#Subfunction for adding a peak to the prototypical mean PARING NEEDED
def account(peak, prototype, i):
	for j in range(max(0,-i),min(len(peak[0]), len(prototype) - i)):
		# print prototype[j+i]
		count(peak[0][j],prototype[j+i])
		# print prototype[j+i]

#The allocation step of k-means clustering
#Now also adds to the prototypical means for the recentering step
def allocate (peaks, means, alignmentMatrix, assignments):
	#Outliers are stored in the first cluster (list) in clusters
	clusters = [[]]
	prototypeLengths = []
	for mean in means:
		clusters += [[mean]]
		prototypeLengths += [0]
	prototypes = initializePrototypes(means)
	for i in range(len(peaks)):
		#the closest mean, instantiated as the first cluster, 0 alignment score
		#if the maxScore changes, the values will be correct,
		#if it doesn't they never get used
		nearest = 0
		maxScore = 0
		alignmentIndex = 0
		alignmentLength = 0
		for j in range(len(means)):
			(index,motifIndex,score,length) = alignmentMatrix[i][j]
			#How to resolve ties?
			if score > maxScore:
				maxScore = score
				nearest = j
				alignmentIndex = index
				alignmentLength = length
		if maxScore <= outlierThreshold:
			group(peaks[i], i, 0, clusters, assignments)
		else:
			#grouping needs nearest+1 because 0 is the outliers
			group(peaks[i], i, nearest+1, clusters, assignments)
			account(peaks[i], prototypes[nearest], alignmentIndex)
			prototypeLengths[nearest] += alignmentLength
	return (clusters, prototypes, prototypeLengths)

#The hell is this and when was it written?  :P
#Reliant on means of the same size....
def difference (prevMean, currMean):
	diff = 0
	for i in range(len(currMean)):
		#This should only go to four - len(currMean[i])
		for j in range(4):
			diff += abs(prevMean[i][j] - currMean[i][j])
	return diff


#if recentered mean moves from seed (previous mean), throw out and pick only from outliers
#recenter on the fly: store number in cluster and just add then average??
#The calculation step of the "centroids" of the clusters
def recenter (clusters, prototypes, prototypeLengths):
	means = []
	for j in range(1,len(clusters)):
		# print clusters[j][0]
		prototype = prototypes[j-1] #take out the outlier cluster
		for loc in prototype:
			total = 0
			for prob in loc:
				# print prob
				total += prob
			#should there ever be a mean without peaks? Throw it out?
			#Also, is it better to have the sum of the values at a location >1?
			# if total != 0: #unnecessary if using prototypes instantiated w/ [1,1,1,1]
				#All locations should have 4 elements, change to len(loc)?
			for p in range(4):
				loc[p] = (loc[p] / total)**2 #try exponentiating the conservation for better alignments
			total = 0
			for prob in loc:
				total += prob
			for p in range(4):
				loc[p] = loc[p] / total
		#now get the mean alignment length
		numPeaks = len(clusters[j])-1
		prototypeLength = prototypeLengths[j-1]
		if numPeaks > 0:
			prototypeLength /= float(numPeaks)
		#Here may be where highly variant means should be thrown out, (before adding new means)
		#but need to allow for the first run with a mean - 
		# the seed will always have high change in variance on the first run
		#ALSO, easier not to change cluster structure before recentering
		clusters[j][0] = (prototype,prototypeLength)
		means += [(prototype,prototypeLength)]
	return means

#perhaps REPLACE THIS with a boolean during alignment
# and a value in the peak data showing the cluster assignment # (check if changed)
def termination(prevAssignments,currAssignments):
	numPeaks = len(currAssignments)
	numReallocated = 0
	for j in range(numPeaks):
		if prevAssignments[j] != currAssignments[j]:
			numReallocated += 1
	return (numReallocated < (numPeaks // 10) + 1)

#The k-means clustering algorithm, managing the termination of clustering under a guessed number of means
def cluster (peaks, means, alignmentMatrix):
	clusters = []
	currAssignments = [0] * len(peaks)
	prevAssignments = list(currAssignments)
	n = 1
	print 'cluster run 1'
	(clusters,prototypes,prototypeLengths) = allocate(peaks,means,alignmentMatrix,currAssignments)
	# print clusters[1][0]
	means = recenter(clusters,prototypes,prototypeLengths)
	# print means[0]
	while not termination(prevAssignments,currAssignments):
		prevAssignments = list(currAssignments)
		alignmentMatrix = align.generate_align_matrix(peaks,means)
		n+=1
		print 'cluster run ' + str(n)
		(clusters,prototypes,prototypeLengths) = allocate(peaks,means,alignmentMatrix,currAssignments)
		# print clusters[1][0]
		means = recenter(clusters,prototypes,prototypeLengths)
	#WIERD to be returning alignmentMatrix &  currAssignments b\c they're one step out of date
	# print means[0]
	# print str(clusters) + '\n'
	return (means,clusters)
