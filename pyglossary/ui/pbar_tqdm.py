# mypy: ignore-errors

from __future__ import annotations

from tqdm import tqdm

__all__ = ["createProgressBar"]


def createProgressBar(title: str):
	return MyTqdm(
		total=1.0,
		desc=title,
	)


class MyTqdm(tqdm):
	@property
	def format_dict(self):
		d = super().format_dict
		# return dict(
		# 	n=self.n, total=self.total,
		# 	elapsed=self._time() - self.start_t
		# 	if hasattr(self, 'start_t') else 0,
		# 	ncols=ncols, nrows=nrows,
		# 	prefix=self.desc, ascii=self.ascii, unit=self.unit,
		# 	unit_scale=self.unit_scale,
		# 	rate=1 / self.avg_time if self.avg_time else None,
		# 	bar_format=self.bar_format, postfix=self.postfix,
		# 	unit_divisor=self.unit_divisor, initial=self.initial,
		# 	colour=self.colour,
		# )
		d["bar_format"] = (
			"{desc}: %{percentage:04.1f} |"
			"{bar}|[{elapsed}<{remaining}"
			", {rate_fmt}{postfix}]"
		)
		# Possible vars:
		# 	l_bar, bar, r_bar, n, n_fmt, total, total_fmt,
		# 	percentage, elapsed, elapsed_s, ncols, nrows, desc, unit,
		# 	rate, rate_fmt, rate_noinv, rate_noinv_fmt,
		# 	rate_inv, rate_inv_fmt, postfix, unit_divisor,
		# 	remaining, remaining_s.
		return d

	def update(self, ratio: float) -> None:
		tqdm.update(self, ratio - self.n)

	def finish(self) -> None:
		self.close()

	@property
	def term_width(self) -> int:
		return self.ncols
