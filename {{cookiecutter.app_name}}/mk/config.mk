SHELL           := bash

YAMLLINT        := yamllint -c .yamllintrc.yaml
AWSCLI          := aws-wrap
CFNLINT         := cfn-lint
CFNNAG          := cfn_nag_scan --input-path
CFVIZ           := python2 cfviz
GRAPHVIZ        := dot -Tpng -o

GIT_REPO        := $(shell git config --get remote.origin.url)
GIT_BRANCH      := $(shell git rev-parse --abbrev-ref HEAD)
GIT_HASH        := $(shell git log -n 1 --pretty=format:'%h')

PREPROCESSOR := gcc -E -x c -P -traditional-cpp

export LC_ALL    = C.UTF-8
export LANG      = C.UTF-8
