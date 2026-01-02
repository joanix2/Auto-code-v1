# Dockerfile for OpenCode AI Service
# Used by Auto-Code backend to execute development tasks in isolated containers

# Start from the latest official Ubuntu release
FROM ubuntu:latest

# Set common environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install core tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core utilities needed for setup and the curl install script
    wget \
    vim \
    ca-certificates \
    curl \
    unzip \
    gnupg \
    sudo \
    git \
    openssh-client \
    # Python and Node.js for common development tasks
    python3 \
    python3-pip \
    nodejs \
    npm

# Install GitHub CLI (gh)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    # Clean up APT lists
    && rm -rf /var/lib/apt/lists/*

# Add the 'ubuntu' user to the sudo group and allow passwordless sudo
RUN usermod -aG sudo ubuntu \
    && echo "ubuntu ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/ubuntu \
    && chmod 0440 /etc/sudoers.d/ubuntu

# Set the existing non-root 'ubuntu' user as the default user
USER ubuntu

# Set the working directory to the user's home folder
WORKDIR /home/ubuntu

# 1. Create the .ssh directory
RUN mkdir -p /home/ubuntu/.ssh

# 2. Add GitHub to the known_hosts file so git commands work non-interactively
RUN ssh-keyscan github.com >> /home/ubuntu/.ssh/known_hosts

# Create the directory structure for the auth file and fix ownership
# This prevents Docker from creating it as 'root' when the volume is mounted.
RUN mkdir -p /home/ubuntu/.local/share/opencode \
    && chown -R ubuntu:ubuntu /home/ubuntu/.local/share/opencode
  
RUN mkdir -p /home/ubuntu/.config/opencode \
    && chown -R ubuntu:ubuntu /home/ubuntu/.config/opencode

# Create workspace directory for repositories
RUN mkdir -p /home/ubuntu/workspace \
    && chown -R ubuntu:ubuntu /home/ubuntu/workspace

# Install OpenCode AI (Native Binary Method)
# https://opencode.ai/docs/
RUN curl -fsSL https://opencode.ai/install | bash

# Expose a port for potential API communication
EXPOSE 8080

# Default command: keep container running
CMD ["/bin/bash"]
