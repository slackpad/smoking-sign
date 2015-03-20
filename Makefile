.PHONY: all
all: test TAGS

TAGS:
	find . -type f -name '*.py' | xargs etags

.PHONY: test
test:
	python -m unittest discover -s . -p '*_test.py'

.PHONY: clean
clean:
	find . -name \*.pyc | xargs rm -f
	rm -f TAGS
