.PHONY: test start stop

all:
	@echo "Top level makefile usage:"
	@echo " make start JIRA_URL=<your_jira_url> JIRA_USER=<usr> JIRA_PASSWORD=<pwd>"

start:
	@docker-compose up -d

stop:
	@docker-compose down

test:
	@docker build --target=test -t jirahack_test .
	@docker run -i -v $(PWD):/test -t jirahack_test
