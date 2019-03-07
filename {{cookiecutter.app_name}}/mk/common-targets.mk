help:
	$(info $(usage))

clean:
	rm -f target/templates/*
	rm -rf target/lambda/*
	rm -f work/templates/*
	rm -f work/*.fragment
	rm -f Makefile.deps
	rm -f diagrams/templates/*

deps: Makefile.deps
	@echo ">>>>>>>>>> Dependencies updated"

Makefile.deps:
	./scripts/gen_deps.sh

release/%: %
	$(PREPROCESSOR) -DGIT_HASH=$(GIT_HASH) \
	                -DGIT_REPO=$(GIT_REPO) \
	                -DGIT_BRANCH=$(GIT_BRANCH) $* > $@

diagrams/%: target/%
	$(CFNFLIP) target/$* | $(CFVIZ) | $(GRAPHVIZ) diagrams/$*.png

lambda/%/requirements.txt: lambda/%/requirements.in
	XDG_CACHE_HOME=/tmp/.pip-cache pip-compile $< -o $@

target/lambda/%: lambda/%/requirements.txt
	mkdir -p $@
	-CFLAGS=-I/usr/include/linux pip install --system --no-compile --no-cache-dir -r $< -t $@

work/%.test.checkpoint: work/%.lint.checkpoint
	$(AWSCLI) cloudformation validate-template --template-body file://target/$*
	touch $@

work/%.lint.checkpoint: target/%
	$(YAMLLINT) target/$*
	$(CFNLINT) target/$*
	$(CFNNAG) target/$*
	touch $@

lint: $(TEMPLATES:%=work/%.lint.checkpoint)
	@echo ">>>>>>>>>> CF templates lint: OK"

test: $(TEMPLATES:%=work/%.test.checkpoint)
	@echo ">>>>>>>>>> CF templates test: OK"

release: $(TEMPLATES:%=release/%)
	@echo ">>>>>>>>>> CF templates release prepared"

diagrams: $(TEMPLATES:%=diagrams/%)
	@echo ">>>>>>>>>> CF diagrams prepared"

# dummy credentials file to make awsecrets happy (dependency of awsspec)
/tmp/.aws/credentials:
	mkdir -p /tmp/.aws
	touch $@

Gemfile.lock:
	HOME=/tmp bundle install --without development --path vendor/bundle

spec: Gemfile.lock /tmp/.aws/credentials
	HOME=/tmp bundle exec rake spec
