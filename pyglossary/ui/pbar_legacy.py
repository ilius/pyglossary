# mypy: ignore-errors

"""
Legacy text progress bar adapter for glossary conversion.

Wraps the vendored ``progressbar`` package to report read/write progress when
``tqdm`` is unavailable or disabled.
"""

from . import progressbar as pb

__all__ = ["createProgressBar"]


def createProgressBar(title: str) -> pb.ProgressBar:
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
