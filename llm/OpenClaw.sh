# 安装 OpenClaw
#!/bin/bash

function installNodeJs() {
  # 下载并安装 nvm：
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  # 代替重启 shell
  \. "$HOME/.nvm/nvm.sh"
  # 下载并安装 Node.js：
  nvm install 24
  # 验证 Node.js 版本：
  node -v # Should print "v24.14.0".
  # 验证 npm 版本：
  npm -v # Should print "11.9.0".
}

function installTools() {
  # 一键装齐编译环境
  yum groupinstall -y "Development Tools"
  yum install -y cmake3
  # 如果装的是 cmake3，需要创建软链接
  ln -sf /usr/bin/cmake3 /usr/bin/cmake
  # 验证
  cmake --version
}

function installOpenClaw() {
  curl -fsSL https://openclaw.ai/install.sh | bash
}

function main() {
  echo "Starting installation... only support CentOS 7.x|alinux x"
  echo "Installing Node.js..."
  installNodeJs
  echo "Installing tools..."
  installTools
  echo "Installing OpenClaw..."
  installOpenClaw
  echo "Installation completed."
}
/etc/cloud/cloud.cfg.d/

main