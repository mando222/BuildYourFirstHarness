run:
	venv/bin/python main.py samples/sample_code.py

clean:
	rm -f state.json report.md
	git checkout samples/sample_code.py

save:
	git stash

.PHONY: run clean save
