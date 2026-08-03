.PHONY: serve build pangu new help

serve:
	@python src/cli.py -s

build:
	@python src/cli.py -d

pangu:
	@python src/cli.py -f

new:
	@python src/cli.py -n $(NAME)

help:
	@echo "make serve    build + live-reload dev server"
	@echo "make build    build static site to public/"
	@echo "make new NAME=slug    create a new draft post"
	@echo "make pangu    format all posts in-place"
