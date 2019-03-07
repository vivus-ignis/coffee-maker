TEMPLATES := $(wildcard templates/*.template.yaml)

$(shell "mkdir" -p work/templates)
$(shell "mkdir" -p target/templates)
$(shell "mkdir" -p target/lambda)
$(shell "mkdir" -p release/templates)
$(shell "mkdir" -p diagrams/templates)

ifndef DEPLOYMENT_ENV
  $(error DEPLOYMENT_ENV undefined)
endif
