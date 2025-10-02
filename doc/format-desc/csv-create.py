import csv

with open("test.csv", "w", encoding="utf-8") as file:
	writer = csv.writer(file)
	for i in range(10):
		writer.writerow(
			[
				f"word{i}",
				f"definition{i}",
				",".join(f"alt{j}" for j in range(4)),
			]
		)
