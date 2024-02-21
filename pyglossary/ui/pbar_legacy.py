# mypy: ignore-errors

from . import progressbar as pb

__all__ = ["createProgressBar"]


def createProgressBar(title: str):
	rot = pb.RotatingMarker()
	pbar = pb.ProgressBar(
		maxval=1.0,
		# update_step=0.5, removed
	)
	pbar.widgets = [
		title + " ",
		pb.AnimatedMarker(),
		" ",
		pb.Bar(marker="█"),
		pb.Percentage(),
		" ",
		pb.ETA(),
	]
	pbar.start(num_intervals=1000)
	rot.pbar = pbar
	return pbar
