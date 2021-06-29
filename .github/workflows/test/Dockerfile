FROM ghcr.io/wadebarnes/indy-plenum/plenum-build:ubuntu-16-04

RUN pip install git+https://github.com/WadeBarnes/indy-plenum.git@publishing-artifacts#egg=indy-plenum[tests]



# ARG GITHUB_REPOSITORY_NAME=hyperledger/indy-plenum
# ARG TAG=ubuntu-16-04
# FROM ghcr.io/$GITHUB_REPOSITORY_NAME/plenum-build:$TAG

# ARG GITHUB_REPOSITORY_NAME
# ARG GITHUB_REF
# RUN pip install git+https://github.com/$GITHUB_REPOSITORY_NAME.git@$GITHUB_REF#egg=indy-plenum[tests]