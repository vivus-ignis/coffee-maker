FROM ubuntu:bionic
RUN apt-get update && apt-get install -y gnupg2 curl ca-certificates
RUN curl -sL "https://keybase.io/crystal/pgp_keys.asc" | apt-key add -
RUN echo "deb https://dist.crystal-lang.org/apt crystal main" > /etc/apt/sources.list.d/crystal.list
RUN apt-get update \
  && apt-get install -y \
  make \
  gawk \
  sed \
  jq \
  git \
  ruby ruby-dev ruby-json \
  python3 python3-dev libffi-dev libssl-dev python3-pip \
  graphviz \
  openssl \
  crystal \
RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN gem install --no-ri --no-rdoc cfn-nag -v 0.3.53
RUN gem install --no-ri --no-rdoc bundler -v 1.17.3
RUN pip3 install \
  yamllint==1.11.1 \
  awscli==1.15.60 \
  cfn-flip==1.0.3 \
  cfn-lint==0.14.0 \
  pip-tools==2.0.2
RUN git clone https://github.com/benbc/cloud-formation-viz.git \
  && cd cloud-formation-viz \
  && git checkout 2806a1729144ca125ae84f1448f7c849949481a1 \
  && cp cfviz /usr/bin/ && chmod +x /usr/bin/cfviz
RUN git clone https://github.com/vivus-ignis/aws-wrap.git \
  && cd aws-wrap \
  && git checkout 476c03ab4dfbf06286f46c4915b90f95b1e6b3d6 \
  && crystal build ./src/aws-wrap.cr \
  && cp ./aws-wrap /usr/bin/
