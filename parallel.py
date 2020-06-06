from pydub import AudioSegment
import glob
import random
import os
from datetime import datetime
import multiprocessing as mp
import sys


noiseSectionLength = 1000; #ms

def makeTrackNoisy(mp3_file, noise_files, lock):

    originalTrack = AudioSegment.from_file(mp3_file)

    for i in range (len(originalTrack)//noiseSectionLength):

        lock.acquire()
        try:
            noiseTrack = AudioSegment.from_file(noise_files[random.randint(0, len(noise_files) - 1)])  # picking random noise file
        finally:
            lock.release()

        msStart = random.randint(0, len(noiseTrack) - noiseSectionLength)                           #picking random part of noise file
        noisePart = noiseTrack[msStart: msStart + noiseSectionLength]

        originalPart = AudioSegment.from_file(mp3_file)[i * noiseSectionLength : (i+1) * noiseSectionLength] #picking i-th part from current voice file

        if (originalPart.dBFS > -50):
            dbShift = originalPart.dBFS - noisePart.dBFS
            noisePart = noisePart + dbShift - random.uniform(2.0, 6.0)
            dbShift = originalPart.dBFS - noisePart.dBFS
            originalPart = originalPart + (4 - dbShift) * random.random()

        if (i == 0):
            mergedTracks = originalPart.overlay(noisePart, position=0)
        else:
            mergedTracks = mergedTracks + originalPart.overlay(noisePart,position=0)

    #print("overlayed, saving");
    mergedTracks.export("./clips/noisy_" + os.path.basename(mp3_file), format="mp3")

def main(mp3_files, noise_files, lock):
    for i, mp3_file in enumerate(mp3_files):
        if (os.path.basename(mp3_file).find("noisy_") == -1):
            makeTrackNoisy(mp3_file, noise_files, lock)

if __name__ == '__main__':

    startTime = datetime.now()

    mp3_files = glob.glob("./clips/*.mp3")
    noise_files = glob.glob("./noises/*.mp3")
    mp3_filesMatrix = []

    try:
        threadsNumber = int(sys.argv[1])
    except IndexError:
        print("NO ARGUMENTS DETECTED")
        print("MAXIMUM THREADS: " + str(mp.cpu_count()))
        exit()

    for i in range (threadsNumber):
        mp3_filesMatrix.append([])


    for i, mp3_file in enumerate(mp3_files):
        mp3_filesMatrix[i % threadsNumber].append(mp3_file)

    lock = mp.Lock()
    processes = []

    for mp3_files in mp3_filesMatrix:
        proc = mp.Process(target=main, args=(mp3_files, noise_files, lock,))
        processes.append(proc)
        proc.start()
        print("Houston, " + str(proc.pid) + " launch")

    for proc in processes:
        proc.join()
        proc.close()
        print("Houston, " + str(proc.pid) + " landed")


    #for i, mp3_file in enumerate(mp3_files):
    #    if (os.path.basename(mp3_file).find("noisy_") == -1):
    #        makeTrackNoisy(mp3_file, noise_files, 25)
    #    printProgressBar(i+1, len(mp3_files), prefix='Progress:', suffix='Complete', length=50)


    print(datetime.now() - startTime)
