import csv
import sys

fpath = sys.argv[1]

inFile = open(fpath, encoding="utf-8")
outFile = open(fpath + ".fixed.csv", "w", encoding="utf-8")

reader = csv.reader(inFile)
writer = csv.writer(outFile)

for row in reader:
	for i in range(1, len(row)):
		row[i] = row[i].replace("\\n", "\n")
	writer.writerow(row)
