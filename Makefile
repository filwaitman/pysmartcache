test:
	flake8 . --max-line-length=120 --exclude=.git
	nosetests tests --with-coverage --cover-package=pysmartcache --cover-inclusive --nocapture ${ARGS}
