.PHONY: run once doctor doctor-warmup

run:
	python -m lkj.cli run

once:
	python -m lkj.cli once --seconds 5

doctor:
	python -m lkj.cli doctor

doctor-warmup:
	python -m lkj.cli doctor --warmup
