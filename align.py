
#how long the words will be
wordLength = 5

#Lower bound for inclusion in high scoring words
highScoreThreshold = 2.0

#Distance that two words must be under to group into a segment pair
segPairWordMaxDist = 12

#The matrix array of characters is a list of [probA;probT;probG;probC] lists
def compare (character, probArray):
	if character == 'A':
		return probArray[0]
	elif character == 'T':
		return probArray[1]
	elif character == 'G':
		return probArray[2]
	elif character == 'C':
		return probArray[3]
	else:
		print "Incorrect string in peaks, implement error handling"

#assume both have the same length, generally = wordLength
def scorePair (seqWord,meanWord):
	#if misalignments become an issue, use weighted mean?
	score = 0
	for i in range(len(seqWord)):
		score += compare(seqWord[i], meanWord[i])
	return score

#Takes a sequence (or mean) and returns the list of words of length wordLength
#Used in the alignment function
def wordify (seq):
	seqWords = []
	for i in range((len(seq)-wordLength+1)):
		seqWords += [seq[i:(i+wordLength)]]
	return seqWords


#Generates an index of alignment, alignment score, and length of the alignment
# in the form (displacement of , alignment index on the mean, score, alignment length)
# where the index is the displacement of the peak sequence from the mean
# weights by length of the alignment relative to the mean length of alignment
# "Length-Sensitive" alignment separately? so non-sensitive first, then after first recen
def align (peak, meanWords, targetLength, targetIndex):
	seqWords = wordify(peak[0])
	scoreMatrix = []
	highScoreWords = []
	for i in range(len(seqWords)):
		scores = []
		for j in range(len(meanWords)):
			score = scorePair(seqWords[i],meanWords[j])
			scores += [score]
			if score > highScoreThreshold:
				highScoreWords += [(score,i,j)]
		scoreMatrix += [scores]
	# print highScoreWords[0]
	# print scoreMatrix
	if len(highScoreWords) > 0:
		segmentPairs = []
		for k in range(len(highScoreWords)):
			(score1,i1,j1) = highScoreWords[k]
			for l in range(k + 1,len(highScoreWords)):
				# print highScoreWords[k]
				# print highScoreWords[l]
				# print '\n'
				(score2,i2,j2) = highScoreWords[l]
				#Second high-scoring word must be close enough, on the same alignment
				dist = abs(i1-i2)
				if (dist < segPairWordMaxDist) and (i1 - i2 + j2 == j1):
					segScore = 0
					# for m in range(dist):
					# 	segScore += scoreMatrix[min(i1,i2)+m][min(j1,j2)+m]
					peakSeg = peak[0][i1:i2+wordLength]
					meanSeg = []
					#This could reaaaally use MEMOIZATION
					for j in range(j1,j2):
						meanSeg += [meanWords[j][0]]
					meanSeg += meanWords[j2]
					#So now, doesn't double-count characters in the center
					# print peakSeg
					# print meanSeg
					segScore = scorePair(peakSeg,meanSeg)
					# print segScore
					if targetLength > 0:
						#accounting for length
						# lengthMultiplier = (targetLength - (targetLength-(float(dist+wordLength)))**2)/targetLength
						# lengthMultiplier = 1 / (1 + (targetLength-(float(dist+wordLength)))**2)
						lengthMultiplier = 1 / (1 + abs(targetLength - float(dist+wordLength))/2.0) #less heavy weighting
							#CONCERN: different motifs may have different variance in alignment length and index
						segScore *= lengthMultiplier
					# (below) the index of the alignment on the mean
					indexOnMean = min(j1,j2)
					if targetIndex >= 0:
						#accounting for alignment index
						# indexMultiplier = 1 / (1 + (targetIndex-(float(indexOnMean)))**2)
						indexMultiplier = 1 / (1 + abs(targetIndex - float(indexOnMean))/2.0) #less heavy weighting
						segScore *= indexMultiplier
					segmentPairs += [(min(j1,j2)-min(i1,i2),indexOnMean,segScore,dist+wordLength)]
		#FIX THIS - sort function? implement search trees for ^ ?
		if len(segmentPairs) > 0:
			# print segmentPairs
			segmentPairs.sort(key = lambda seg: seg[2], reverse=True)
			# print segmentPairs
			return segmentPairs[0]
		highScoreWords.sort(reverse=True)
		(score,i,j) = highScoreWords[0]
		if targetLength > 0:
			#accounting for length
			# lengthMultiplier = (targetLength - (targetLength-(float(wordLength)))**2)/targetLength
			# lengthMultiplier = 1 / (1 + (targetLength-(float(wordLength)))**2)
			lengthMultiplier = 1 / (1 + abs(targetLength - float(wordLength))/2.0)
			score *= lengthMultiplier
		if targetIndex >= 0:
			#accounting for alignment index
			# indexMultiplier = 1 / (1 + (targetIndex-(float(j)))**2)
			indexMultiplier = 1 / (1 + abs(targetIndex - float(j))/2.0)
			score *= indexMultiplier
		return (j-i,j,score,wordLength)
	return (0,0,0,0)


# def align_mean (peak, mean):
# 	return align(peak, wordify(mean))

#kinda sad functions, index is only used in recentering,
# and only the score is used everywhere else: so separate them entirely?
def index_of_align(peak, meanWords, targetLength, targetIndex):
	(i,m,score,length) = align(peak,meanWords,targetLength,targetIndex)
	return i

def score_of_align(peak, meanWords, targetLength, targetIndex):
	(i,m,score,length) = align(peak,meanWords,targetLength,targetIndex)
	return score


#Generates an alignment matrix using length sensitive alignments
def generate_align_matrix(peaks,means):
	meanWordsList = []
	for (mean,targetLength,targetIndex) in means:
		meanWordsList += [(wordify(mean),targetLength,targetIndex)]
	alignmentMatrix = []
	for i in range(len(peaks)):
		peak = peaks[i]
		peakAlignments = []
		for j in range(len(means)):
			(meanWords,targetLength,targetIndex) = meanWordsList[j]
			peakAlignments += [align(peak,meanWords,targetLength,targetIndex)]
		alignmentMatrix += [peakAlignments]
	return alignmentMatrix

#An alignment matrix for variance and mean paring calculations
def generate_var_align_matrix(clusters):
	alignmentMatrix = []
	for j in range(len(clusters)-1):
		cluster = clusters[j+1]
		# print cluster[0]
		(mean,targetLength,targetIndex) = cluster[0]
		meanWords = wordify(mean)
		peakAlignments = []
		for i in range(len(cluster)-1):
			peak = cluster[i+1]
			peakAlignments += [align(peak,meanWords,targetLength,targetIndex)]
		alignmentMatrix += [peakAlignments]
	return alignmentMatrix

# def generate_align_matrix(peaks,means):
# 	meanWordsList = []
# 	for mean in means:
# 		meanWordsList += [wordify(mean)]
# 	alignmentMatrix = []
# 	for i in range(len(peaks)):
# 		peak = peaks[i]
# 		peakAlignments = []
# 		for j in range(len(means)):
# 			peakAlignments += [align(peak,meanWordsList[j])]
# 		alignmentMatrix += [peakAlignments]
# 	return alignmentMatrix