import align
import cluster

import random
import math

import scipy
from scipy import stats


#The p-value to check against to stop the clustering algorithm. Change this
probabilityThreshold = .05

#Use an asymptotic function with the Welch's t-test p-value as a seed for
#how far along the function to pick (closer to stable -> fewer new means)
#def calcSubSize (k,n):

def calcSubSize (numMeans, numPeaks):
	#deal with the case where the subsample or the number of peaks left
	#is less than the number of new guessed clusters [+5 below]
	subSize = numPeaks//10 + 5
	return subSize

#Takes a random peak and removes it from the list of peaks,
#returns (peak, remaining peaks) as a tuple
def sample (peaks):
	index = random.randrange(len(peaks))
	return (peaks.pop(index),peaks)

def minScore (peak, meanWordsList):
	#align gives a tuple of index, score, so take the score
	minVal = align.score_of_align(peak, meanWordsList[0])
	for meanWords in meanWordsList[1:]:
		minVal = min(minVal, align.score_of_align(peak,meanWords))
	return minVal

def kPlusPlus (means, peaks):
	meanWordsList = []
	for mean in means:
		meanWordsList += [align.wordify(mean)]
	seedIndex = 0
	minVal = minScore(peaks[0], meanWordsList)
	for i in range(1,len(peaks)):
		#Bias? should this be randomized instead?
		tempScore = minScore(peaks[i], meanWordsList)
		if tempScore < minVal:
			minVal = tempScore
			seedIndex = i
	return (peaks.pop(seedIndex),peaks)

#The matrix array of characters is a list of [probA;probT;probG;probC] lists
def initProb (character):
	if character == 'A':
		return [1,0,0,0]
	elif character == 'T':
		return [0,1,0,0]
	elif character == 'G':
		return [0,0,1,0]
	elif character == 'C':
		return [0,0,0,1]
	else:
		print "Incorrect string in peaks, implement error handling"

# def initProb (character):
# 	if character == 'A':
# 		return [5,1,1,1]
# 	elif character == 'T':
# 		return [1,5,1,1]
# 	elif character == 'G':
# 		return [1,1,5,1]
# 	elif character == 'C':
# 		return [1,1,1,5]
# 	print "Incorrect string in peaks, implement error handling"

#abstracts a peak seed into a mean
def abstract(peak):
	seq = peak[0]
	matrix = []
	for character in seq:
		matrix += [initProb(character)]
	return matrix

# picks a subsample from peaks, 
# then picks seed means from that by k++ w/o replacement
# Need to implement what happens when numMeans > len(peaks)
def pickMeans (peaks, numMeans):
	#New object with list() - not an alias
	nonReplacement = list(peaks)
	subSample = []
	subSampleSize = calcSubSize(numMeans, len(peaks))
	for x in xrange(subSampleSize):
		(thisPeak,rest) = sample(nonReplacement)
		nonReplacement = rest
		subSample += [thisPeak]
	#Now we create the list of new means
	seeds = []
	(seed, subSample) = sample(subSample)
	seeds += [abstract(seed)]
	for i in range(numMeans - 1):
		(seed, subSample) = kPlusPlus(seeds,subSample)
		seeds += [abstract(seed)]
	return seeds


# try storing prev. cluster variance? - in main
def variance (cluster):
	sumVar = 0
	meanWords = align.wordify(cluster[0])
	for seq in cluster[1:]:
		sumVar += align.score_of_align(seq, meanWords)
	#Integer division is // while / does floating point
	#What do you do if NOTHING gets clustered with the mean?
	if len(cluster) > 1:
		return (sumVar / (len(cluster) - 1))
	else:
		return 0

# returns the standard deviation of a cluster
# measured by alignment score from the mean
def stdDev (cluster):
	return math.sqrt(variance(cluster))

#Tie this to subsample in the future - you need 
def guessInitMeans(peaks):
	return 5

#Guesses how many more means will be needed
#Just iterates by 5. Ouch.
def guessNewMeans(peaks, means):
	return 5

def welchTest (prevClusters,currClusters):
	prevClusterVariances = []
	currClusterVariances = []
	for cluster in prevClusters[1:]:
		prevClusterVariances += [variance(cluster)]
	for cluster in currClusters[1:]:
		currClusterVariances += [variance(cluster)]
	(t_stat,p_val) = scipy.stats.ttest_ind(prevClusterVariances, currClusterVariances, equal_var = False)
	return p_val

#temporary initial step for the welch's test (?)
def clustrifyMeans (means):
	listifiedMeans = []
	for i in range(len(means)):
		#Double brackets, as single brackets just recostructs means
		listifiedMeans += [[means[i]]]
	# print listifiedMeans[0]
	return listifiedMeans

# print a line when the variance goes back up between means
# Requires a list of peaks where the sequence is the first element of the peak
def main (peaks):
	prevClusters = []
	means = pickMeans(peaks,guessInitMeans(peaks))
	print means[0]
	#The extra list at the beginning is for outliers,
	#and is initialized with all peaks
	currClusters = [peaks] + clustrifyMeans(means)
	#Aliasing issues? lists within lists?
	prevClusters = list(currClusters)
	print 'first runthrough of clustering'
	(means,currClusters) = cluster.cluster(peaks,means)
	print 'starting welch\'s t-test clustering with centroid means'
	while welchTest(prevClusters,currClusters) > probabilityThreshold:
		numNewMeans = guessNewMeans(peaks, means)
		outliers = currClusters[0]
		means += pickMeans(outliers,numNewMeans)
		prevClusters = list(currClusters)
		(means,currClusters) = cluster.cluster(peaks,means)
		print 'finished clustering of subsequent k guess'
	return currClusters