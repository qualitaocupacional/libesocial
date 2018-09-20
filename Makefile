.PHONY: clean

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm dist/*

release:
	python setup.py sdist bdist_wheel

dist-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

distribution:
	twine upload dist/*
