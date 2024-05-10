FROM registry.access.redhat.com/ubi9/ubi:latest as base

ARG USERNAME=""
ARG USER_UID=1009
ARG USER_GID=$USER_UID
ARG WORKING_DIR_NAME="/home/${USERNAME}/project"
ARG OUTPUT_DIR_NAME="/home/${USERNAME}/IBM-lpar_consistency_output"
ARG SSH_DIR="/home/${USERNAME}/.ssh"
ARG LIST_DIR="/home/${USERNAME}/lists"

RUN /usr/sbin/groupadd --gid $USER_UID $USERNAME \
    && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN mkdir -p "${WORKING_DIR_NAME}" && \
    mkdir  "${OUTPUT_DIR_NAME}" && \
    mkdir  "${SSH_DIR}" && \
    mkdir  "${LIST_DIR}" && \
    chmod 700 "${SSH_DIR}" && \
    chmod -R 777 "${OUTPUT_DIR_NAME}" && \
    chown -R ${USERNAME}:${USER_GID} "${OUTPUT_DIR_NAME}"

# Install any possibly needed compile time packages
RUN dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    dnf install -y --setopt=tsflags=nodocs \
                    cmake \
                    openssh-server \
                    openssl-devel \
                    gcc \
                    g++ \
                    rust \
                    cargo \
                    python-devel \
                    platform-python-devel \
                    less \
                    lsof \
                    python3-pip \
                  --exclude container-selinux && \
    dnf clean all && \
    ln -s /usr/bin/python3 /usr/bin/python

COPY ../. ${WORKING_DIR_NAME}
COPY ./.ssh ${SSH_DIR}

# Install any pip required packageds from REQ
RUN pip install -r ${WORKING_DIR_NAME}/requirements.txt

RUN chown -R "${USERNAME}":"${USER_GID}" "/home/${USERNAME}" && \
    ls -lart "/home/${USERNAME}"

EXPOSE 22

USER ${USERNAME}
WORKDIR ${WORKING_DIR_NAME}

CMD ["python", "src/checker.py"]
