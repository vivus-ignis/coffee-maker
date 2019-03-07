define usage :=

Usage:
------
lint            : perform static analysis of templates
test            : validate templates using AWS API
install, deploy : deploy to AWS environment
deploy-base     : deploy base stack only
release         : compile templates
diagrams        : generate graphviz diagrams for templates
clean           : wipe out all the caches
endef

define eb_deploy
	$(AWSCLI) elasticbeanstalk create-application-version \
	  --application-name "${DEPLOYMENT_ENV} $(1)" \
	  --version-label $(2) \
	  --source-bundle S3Bucket=${DEPLOYMENT_BUCKET},S3Key=$(3) \
	  --process
	env_name=`$(AWSCLI) elasticbeanstalk describe-environments \
	  --application-name "${DEPLOYMENT_ENV} $(1)" \
	| jq -r '.Environments[].EnvironmentName'` \
	&& $(AWSCLI) elasticbeanstalk update-environment \
	  --environment-name "$$env_name" \
	  --version-label $(2)
	PYTHONUNBUFFERED=x python3 ./scripts/eb_waiter.py "${DEPLOYMENT_ENV} $(1)"
	PYTHONUNBUFFERED=x python3 ./scripts/eb_events_checker.py "${DEPLOYMENT_ENV} $(1)"
endef
