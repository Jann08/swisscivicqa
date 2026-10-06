# Judges: `make run` from the repository root delegates to the challenge directory.
.PHONY: run full test
run full test:
	$(MAKE) -C track_1b $@
