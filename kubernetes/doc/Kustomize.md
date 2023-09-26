# 通过 Kustomize 的配置管理

## 一、了解 Kustomize

`Kustomize` 的代码库 [GitHub 地址](https://github.com/kubernetes-sigs/kustomize)。Kustomize 是 Kubernetes 原生配置管理工具，实现了类似 sed 的给资源配置文件"打补丁"的能力。Kubernetes 1.14.0 版本已经集成到了 kubectl 命令中，所以也可以通过 kubectl 的子命令来使用Kustomize.

### 1. Kustomize 的基本概念

- Kustomize 中的几个关键术语
    - kustomization 这个词指代的是一个 kustomization.yaml 文件
        - 或者更广义地理解为一个包含 kustomization.yaml 文件的目录以及这个 kustomization.yaml 文件中引用的所有其他文件
    - base 指的是被其他 kustomization 引用的一个 kustomization 
        - 换言之，任何一个kustomization a被另一个kustomization b引用时，a是b的base，
        - 这时如果新增一个kustomization c来引用b，那么b也就是c的base
        - 即，base是一个相对的概念，而不是某种属性标识
    - overlay 与base相对应，依赖另一个kustomization的kustomization被称为overlay
        - 如果kustomization b引用了kustomization a，那么b是a的overlay，a是b的base


## 二、使用 Kustomize

### 1. Kustomize 的安装

Kustomize 提供了 Linux/Darwin 系统 *amd64/arm64 架构的二进制可执行文件(Windows等也支持，不过不建议在Windows上使用这些工具)。可以到Kustomize项目的 [release](https://github.com/kubernetes-sigs/kustomize/releases)页面去下载对应的压缩包。