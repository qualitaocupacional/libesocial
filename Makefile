.PHONY: clean

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

release:
	python setup.py sdist bdist_wheel
