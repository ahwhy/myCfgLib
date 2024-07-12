# GPU 笔记

## 一、了解 GPU

### 1、GPU

图形处理器(graphics processing unit，缩写 GPU)，又称显示核心、视觉处理器、显示芯片，是一种专门在个人电脑、工作站、游戏机和一些移动设备(如平板电脑、智能手机等)上做图像和图形相关运算工作的微处理器。

相比CPU、内存来说，GPU是一个外围设备，是一个协处理器，它没有像CPU那样的控制权限。GPU上有专供自己使用的内存(一般笼统的称为显存)和计算单元(比如应用于张量计算的Tensor Core、32浮点数计算引擎等)。

由于GPU是与CPU分离的，且GPU没有总线控制权，故 GPU 运算时必须先将 CPU 端的代码和数据传输到 GPU，GPU 才能执行 kernel 函数(在GPU上运行的代码称为核函数)。

整个处理数据流处理流程如下: 
- CPU发出命令将内存的数据拷贝到GPU的显存里
- CPU通知GPU执行运算
- GPU运算完成后，将数据存入GPU的显存内
- CPU发出命令，将数据从显存拷贝到内存里，获得结果

### 2、CUDA

CUDA(Compute Unified Device Architecture，统一计算设备架构)，是显卡厂商NVIDIA在2007年推出的并行计算平台和编程模型。它利用图形处理器(GPU)能力，实现计算性能的显著提高。

CUDA的软件堆栈由三层构成: 
- CUDA Driver API: CUDA驱动层的API，功能最全，但是使用十分复杂。一般给一些与GPU硬件打交道的人使用。
- CUDA Runtime API: 封装了一些驱动的API，将某些驱动初始化操作隐藏起来，使用起来更方便一些。
- CUDA Library: 一些常用函数的集合，比如我需要做一个矩阵乘的运算，我不必从头到尾实现这个函数，直接调用它提供的矩阵乘函数即可。

其中 CUDA Driver API 由 NVIDIA Driver包提供，而 CUDA Library 和 CUDA Runtime 由 CUDA Toolkit包提供。


## 二、GPU的使用

### 1、容器中使用GPU
在主机上直接运行CUDA程序时，需要在主机安装GPU驱动和CUDA Toolkit。例如在一个GPU服务器中初始化GPU方面的配置，需要安装[NVIDIA GPU Driver(CUDA Driver)](https://www.nvidia.com/download/index.aspx)与CUDA Toolkit

而在容器中使用GPU设备时，架构发生了变化: 
- 主机仅安装NVIDIA GPU Driver(CUDA Driver)。
- 容器中安装CUDA Toolkit，可以使用NVIDIA提供的CUDA Base镜像(https://hub.docker.com/r/nvidia/cuda)，这些镜像已经安装好了CUDA Toolkit，基于这些Base镜像构建需要的镜像即可。