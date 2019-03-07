include mk/init.mk
include mk/config.mk
include mk/functions.mk

{% if cookiecutter.use_reduced_costs_flag == "y" -%}
ifeq ($(DEPLOYMENT_ENV),dev)
  PREPROCESSOR := $(PREPROCESSOR) -DREDUCED_COSTS
endif
{%- endif %}

-include Makefile.deps
include mk/common-targets.mk

deploy-base: Makefile.deps work/templates/Base.template.yaml.test.checkpoint
	$(AWSCLI) cloudformation deploy \
	  --template-file target/templates/Base.template.yaml \
	  --stack-name ${DEPLOYMENT_ENV}-{{cookiecutter.app_name}}-base \
	  --no-fail-on-empty-changeset \
	  --capabilities CAPABILITY_IAM \
	  --parameter-overrides \
	  ApplicationEnvironment=${DEPLOYMENT_ENV}

deploy: Makefile.deps test .rds-master-user-password .rds-app-user-password
	set -o pipefail ; \
	$(AWSCLI) cloudformation deploy \
	  --no-fail-on-empty-changeset \
	  --template-file target/templates/Base.template.yaml \
	  --stack-name ${DEPLOYMENT_ENV}-{{cookiecutter.app_name}}-base \
	  --no-fail-on-empty-changeset \
	  --capabilities CAPABILITY_IAM \
	  --parameter-overrides \
	  ApplicationEnvironment=${DEPLOYMENT_ENV} \
{%- if cookiecutter.use_rds == "y" %}
	| $(AWSCLI) cloudformation deploy \
	  --no-fail-on-empty-changeset \
	  --template-file target/templates/DB.template.yaml \
	  --stack-name ${DEPLOYMENT_ENV}-{{cookiecutter.app_name}}-db \
	  --no-fail-on-empty-changeset \
	  --parameter-overrides \
	  RDSMasterUserName="postgres" \
	  RDSMasterUserPassword=`ruby -e 'print File.open(".rds-master-user-password").read'` \
	  ApplicationEnvironment=${DEPLOYMENT_ENV} \
	  RDSSnapshotIdentifier=${RESTORE_FROM_SNAPSHOT} \
{%- endif %}
{%- if cookiecutter.use_elasticbeanstalk == "y" %}
	| $(AWSCLI) cloudformation deploy \
	  --no-fail-on-empty-changeset \
	  --template-file target/templates/AppElasticBeanstalk.template.yaml \
	  --stack-name ${DEPLOYMENT_ENV}-{{cookiecutter.app_name}}-app \
	  --no-fail-on-empty-changeset \
	  --capabilities CAPABILITY_IAM \
	  --parameter-overrides \
	  KeyPair="${DEPLOYMENT_ENV}-{{cookiecutter.app_name}}" \
	  ApplicationEnvironment=${DEPLOYMENT_ENV} \
	  AppDatabaseUserName="app_user" \
	  AppDatabaseUserPassword=`ruby -e 'print File.open(".rds-app-user-password").read'` \
{%- endif %}

{% if cookiecutter.use_elasticbeanstalk == "y" -%}
app-eb-deploy:
	$(call eb_deploy,{{cookiecutter.app_name}},${APP_VERSION},{{cookiecutter.app_name}}.${APP_VERSION}.war)
{%- endif %}

.PHONY: help lint test deps release clean spec \
{% if cookiecutter.use_elasticbeanstalk == "y" -%}
  deploy deploy-base app-eb-deploy
{% else -%}
  deploy deploy-base
{%- endif %}

.SECONDARY: Makefile.deps Gemfile.lock
.PRECIOUS: target/% lambda/target/%/ lambda/%/requirements.txt
