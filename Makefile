HUGO = hugo
PORT = 1313
BUILD_DIR = public

.PHONY: serve build clean push new check

serve:
	$(HUGO) server -D -p $(PORT)

build: clean
	$(HUGO)

clean:
	rm -rf $(BUILD_DIR)

push:
	@if git status --porcelain | grep '^[? ]' >/dev/null; then \
		git add . && \
		read -p "Commit message: " msg && \
		git commit -m "$$msg" && \
		git push origin main; \
	else \
		echo "No changes to commit"; \
	fi

new:
	@if [ -z "$(TITLE)" ]; then \
		echo "Please specify title, e.g.: make new TITLE='New Post Title'"; \
		exit 1; \
	fi
	$(HUGO) new content/p/$(shell echo "$(TITLE)" | tr '[:upper:] ' '[:lower:]-').md

check:
	$(HUGO) check
