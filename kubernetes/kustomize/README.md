# 通过 Kustomize 的配置管理

## 了解 Kustomize

`Kustomize` 的代码库 [GitHub 地址](https://github.com/kubernetes-sigs/kustomize)。Kustomize 是 Kubernetes 原生配置管理工具，实现了类似 sed 的给资源配置文件"打补丁"的能力。Kubernetes 1.14.0 版本已经集成到了 kubectl 命令中，所以也可以通过 kubectl 的子命令来使用Kustomize.

### Kustomize 的基本概念

- Kustomize 中的几个关键术语
    - kustomization 这个词指代的是一个 kustomization.yaml 文件
        - 或者更广义地理解为一个包含 kustomization.yaml 文件的目录以及这个 kustomization.yaml 文件中引用的所有其他文件
    - base 指的是被其他 kustomization 引用的一个 kustomization 
        - 换言之，任何一个 kustomization a 被另一个 kustomization b 引用时，a 是 b 的 base，
        - 这时如果新增一个 kustomization c 来引用 b，那么 b 也就是 c 的base
        - 即，base是一个相对的概念，而不是某种属性标识
    - overlay 与 base 相对应，依赖另一个 kustomization 的 kustomization 被称为 overlay
        - 如果 kustomization b 引用了 kustomization a，那么 b 是 a 的 overlay，a 是 b 的 base


## 传送门

- [通过 Kustomize 的配置管理](./Kustomize.md)