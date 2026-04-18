.PHONY: gui daemon run once doctor doctor-warmup

gui:
	python -m lkj.cli gui

daemon:
	python -m lkj.cli daemon

run:
	python -m lkj.cli daemon

once:
	python -m lkj.cli once --seconds 5

doctor:
	python -m lkj.cli doctor

doctor-warmup:
	python -m lkj.cli doctor --warmup
