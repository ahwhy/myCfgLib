# 大模型相关

## 一、大模型

### 1、大模型的一些基础知识点

#### 大模型

大模型（LLM Large Language Model）狭义上指基于深度学习算法进行训练的自然语言处理（NLP）模型，主要应用于自然语言理解和生成等领域，广义上还包括机器视觉（CV）大模型、多模态大模型和科学计算大模型等。

AI 大模型 (AI Large Models)
├── LLM (大型语言模型)  ← 最主流，处理文本/代码
├── LMM (大型多模态模型)  ← 处理文本 + 图像/视频/音频
├── 视觉大模型  ← 专门处理图像 (如 SAM)
└── 科学大模型  ← 专门处理生物/物理/化学 (如 AlphaFold)

Transformer 是一种用于序列到序列（Seq2Seq）任务的深度学习模型架构，由 Vaswani 等人于 2017 年 在论文《Attention is All You Need》中提出 15。在大语言模型（LLM）的架构中，Transformer 扮演着关键角色，它是模型的核心组件，负责处理文本序列的建模和处理


#### 大模型迭代的具体过程（Scaling Law）

不能"边训练边加参数"，比如从 7B 到 70B ，这个开发过程，遵循缩放定律（Scaling Laws）。

第一步：设计架构（定参数）
工程师在代码配置文件（如 config.json）中设定好：
层数 (Layers)：7B 可能是 32 层，70B 可能是 80 层。
隐藏层维度 (Hidden Size)：7B 可能是 4096，70B 可能是 8192。
注意力头数 (Attention Heads)：相应增加。
计算结果：这些数字相乘，直接决定了参数量是 70 亿还是 700 亿。这一步发生在训练第 1 步之前。

第二步：准备数据（喂知识）
7B 模型可能只需要 2 万亿 token 的数据就能吃饱。
70B 模型则需要 10 万亿甚至更多的数据。
参数越多，需要的"食物"（数据）就越多。如果给 70B 模型只喂 7B 的数据，它会"营养不良"（过拟合），表现反而不如 7B。

第三步：训练（填数值）
启动成千上万张显卡，开始计算。
这个过程可能持续几个月。
训练结束时，这 700 亿个参数的数值被确定了，但数量从头到尾没变过。
第四步：评估与下一代
如果发现 70B 效果很好，但成本太高，下一代可能设计一个 397B 的 MoE 模型（总参数多，但每次只用一部分）。
这又是新一轮的架构设计和重新训练。


#### 大模型的一些分类
稠密模型 (Dense)：比如 70B 就是实打实 70B，每次计算都用全部参数。

混合专家模型 (MoE)：
随着应用场景的复杂化和细分化，大模型要处理的问题逐渐多元化，遍及计算机、法律、医疗等各个专业领域，大模型的参数规模和复杂度也在不断增长。仅使用传统的单一大模型，会导致模型训练和推理时间变得更高、模型响应效率降低，在多模态大模型中尤为突出。为了解决这些问题，混合专家模型（Mixture of Experts，简称MoE）应运而生。
简单来说，混合专家模型的核心思想就是术有专攻，类似"专家会诊"，由多个不同领域的模型（即"专家"）组合成一个模型，分别去解决不同领域的问题。
混合专家模型主要由以下2个核心组件共同协作：
● Experts（专家网络）：每个专家网络是用来处理某一特定类型问题或数据子集的独立模型，一般都在他们各自的专长上受过训练，推理时只有部分专家网络参与计算。
● GateNet（门控网络）：类似于"交通指挥官"，负责评估输入数据，并决定由哪些专家参与处理当前的问题，尽可能地利用每个专家的专业知识来提供最准确的预测或决策输出。
比如：总参数 397B（比如 拥有 100 个专家网络）。
激活参数：每次回答只调用其中 2 个专家（比如实际计算量相当于 50B）。
迭代方式：工程师可以在训练过程中，增加专家的数量（从 8 个专家增加到 16 个专家）。
理解：这就像公司原本有 8 个部门，后来扩招到 16 个部门。虽然总人数（总参数）增加了，但每次处理任务还是只派 2 个部门去。这需要特定的训练技巧，但依然是在训练阶段完成的，而不是模型发布后自己增长。

混合专家模型的局限
尽管混合专家模型在处理复杂任务和提高模型性能方面表现出众，但它们也有一些局限性：
● 计算资源需求高：MoE模型中的每个专家都是一个独立的模型，当专家数量增加时，模型的总参数量也相应增加，导致部署模型可能需要更多的GPU显存资源。
● 过拟合风险：由于参数量大和复杂性，可能比简单模型更容易过拟合训练数据，特别是当数据量不足时。

多模态大模型：
每一种信息的来源或者形式，都可以称为一种模态（Modality）。例如，人类会通过色香味点评食物，并通过文字和图片记录。这里的视觉、嗅觉、味觉、文字、图片都是不同的模态。
而在大模型领域，模态指的是数据或信息的类型或表达形式，文本、图像、视频、音频等都是不同的模态。
多模态，顾名思义，就是指结合两种及以上的模态，进行更综合的数据处理和分析。如果想要大模型真正模拟人类，实现多形式的输入和生成，单一类型的数据处理已经无法满足，大模型需具备同时处理和理解多种类型数据的能力。
大模型本身也可以是多模态的，也就是多模态大模型，有同时处理多模态数据（如文本、图像、音频等）和执行复杂任务的能力，比如文生图、语音识别、图像字幕等。

大小模型云端协同
模型的大小通常与模型的规模、复杂度和参数数量有关，无论是大模型还是小模型，都各有优劣。
"大模型"，顾名思义，参数规模庞大且结构复杂度高，能处理复杂的任务，准确率和泛化能力强，训练和推理需要大量的计算资源和时间，不适合直接部署在资源受限的设备上（如移动设备）。
与之对应的就是"小模型"，参数规模较小、计算密度较低，在性能上可能不及大模型，但对比大模型，训练和推理的资源需求较低，响应速度更快，适合在资源受限的环境下运行，如移动设备、边缘计算设备。
然而，在实际应用中，一个系统通常需要同时考虑到性能、响应效率、数据隐私、成本和资源使用效率，单独使用大模型或小模型很难满足所有这些需求。例如，一个电商APP为亿级用户提供服务，如果仅用单一超大模型提供服务，日常每秒超过万次请求，峰值每秒超过10万次请求，如果遇到服务高峰期，一次请求的延时可能会超过一分钟，严重影响用户体验。
2022年十大科技趋势提出大小模型云端协同的概念，将大模型部署在云端，向边、端的小模型输出模型能力，小模型负责实时数据处理和初步推理，并向大模型反馈算法与执行成效，这样既能在云端充分发挥大模型的推理训练能力，又能调动边、端的小模型的敏捷性，可实现合理分配计算资源、提高响应速度。


#### 关于提示词
提示词可以包含以下任意要素：
指令 Instruction：需要模型去做什么，如回答某个问题、撰写某种类型的文章或按照特定格式进行总结。指令应该简洁、明确，确保 LLM 能够理解任务的目标和要求。
背景信息 Context：背景信息可以包括任务的背景、目的相关的各类信息，还可以为 LLM 设置角色背景、观点立场等信息，LLM 将在此背景下进行回应或生成文本。
参考样本 Examples：与解决用户问题相关的示例，比如通过少样本提示的方式帮助 LLM 更好理解如何处理指令。
输入数据 Input Data：用户输入指令和要求，比如用什么语气，生成多少字的内容。
输出指示 Output Indicator：指定输出的类型或格式，我们可以给出限定关键词、限制条件或要求的输出格式/方式（如表格），也可以避免无关或不期望的信息出现。

结合上述要素，我们可以根据任务的复杂度来设计提示词，具体有以下几种情况：
1. 纯指令型：最直接的互动方式，仅通过简明指令向模型提出需求，适合于寻求快速、基本答案的场景。
2. 背景+指令：在指令基础上融入背景信息，为模型创造一个理解和响应任务的框架，尤其适用于需要考虑特定情境或角色定位的任务。
3. 指令/背景+输出指示：在基础指令或背景信息之上，加入输出指示，精确指导模型如何组织和呈现答案，以满足特定的格式或风格要求。
4. 综合型提示：结合指令、背景信息、输入数据与输出指示，形成一个全方位的引导体系。这种复合型提示尤为强大，能够在复杂任务中提高模型输出的针对性与质量，尤其是在模型需要从示例中学习并模仿特定风格或结构时

常见提示词框架及场景
CRISPE
项目管理、团队协作、客户服务
能力 (Capabilities)
角色 (Roles)
洞察 (Insights)
陈述 (Statement)
个性 (Personality)
实验 (Experiment)

ROSES
软件开发、产品设计、市场营销策略规划
角色 (Role)
目标 (Objective)
场景 (Setting)
预期解决方案 (Expected Solution)
步骤 (Steps)

TRACE
市场研究、业务分析、教学设计
任务 (Task)
请求 (Request)
操作 (Action)
上下文 (Context)
示例 (Examples)


### 2、RAG - 通过 RAG 增强大模型
检索增强生成包括三个步骤，建立索引、检索、生成。

RAG主要由两个部分构成：
建立索引：首先要清洗和提取原始数据，将 PDF、Docx 等不同格式的文件解析为纯文本数据；然后将文本数据分割成更小的片段（chunk）；最后将这些片段经过嵌入模型转换成向量数据（此过程叫做embedding），并将原始语料块和嵌入向量以键值对形式存储到向量数据库中，以便进行后续快速且频繁的搜索。这就是建立索引的过程。
检索生成：系统会获取到用户输入，随后计算出用户的问题与向量数据库中的文档块之间的相似度，选择相似度最高的K个文档块（K值可以自己设置）作为回答当前问题的知识。知识与问题会合并到提示词模板中提交给大模型，大模型给出回复。这就是检索生成的过程。
提示词模板类似于：请阅读：{知识文档块}，请问：{用户的问题}


### 3、通过微调改善大模型在垂直领域的表现


#### 3.1 什么是微调
核心思想：在预训练的基础上，使用特定领域的数据对模型进行进一步的训练，从而让模型更擅长处理你想要解决的问题，也就是说，让大模型更懂你。


#### 3.2 微调能实现什么
● 风格化（如角色扮演）：
假设你有一个通用的大模型，它对各种话题都有所了解。但你想要让它作为医疗专家，专职回答医疗问题：即不仅可以理解病患的问题，还可以通过一两句话就能切中要害、直指问题并给出方案。
那么你可以通过微调大模型，用大量的医学文献和医疗病例对其进行训练，从而让大模型更准确地理解医学术语，给出专家建议。
● 格式化（如系统对接）：
假设你需要开发一个智能助理，对接一个很复杂的系统，这个系统具有诸多业务接口和复杂的API规范。根据之前的学习，你可能会想到以下方案：
    ‒ 给大模型提供相关文档片段，你可能会遇到：由于原始文档结构有比较复杂的结构，或者知识点比较分散，导致检索效果不好，应用程序不能一次性把准确的API规范提供给大模型。
    ‒ 把整本的API手册一次性塞给大模型，你可能会遇到：大模型允许输入的上下文Tokens很可能被占满。超出部分被截断，结果大模型没有看到有效API规范。
    ‒ 使用一个支持1000万tokens以上的大模型服务。但如果每次用户请求服务时，系统后台都要把整本API文档交给大模型服务，去处理一些"日常小任务"，这又会造成极大的资源浪费。而且，过大的提示词也会导致系统的响应速度下降，导致用户体验变差。或者同样由于文档结构复杂和信息分散，"噪音过多"，大模型看遍整本API手册，也没有看到有效的API规范。
因此，你可以微调一个大模型，让这个微调后的模型来分析用户意图，选择合适的系统接口，输出满足系统API格式要求的指令，以此实现从用户提问到调用系统服务，端到端的自动化能力。


#### 3.3 为什么要微调？提高效率和降低成本：

微调（Fine-tuning），你可能在使用Qwen-72B-chat模型来处理某个文本分类任务。由于模型参数量较大，文本分类的准确率非常高，但同样因为参数量较大，模型的推理成本和耗时都比较高。为了达到近似的效果，并且降低推理成本和耗时，你可以直接使用Qwen-1.8B-chat模型来处理这个分类任务，尽管推理成本和耗时低很多，但分类准确度可能也会低很多。此时，你可以尝试通过一个文本分类数据集对其进行微调，让微调后的Qwen-1.8B-chat模型在分类任务中的表现接近Qwen-72B-chat。虽然牺牲了可接受范围的准确度，但是成本和推理速度获得了极大改善。


#### 3.4 微调的关键
● 需要特定领域的高质量数据：只有收集到高质量的数据，微调后的模型才可能会表现出色，但是高质量的数据往往并不容易获得，收集的过程可能会带来成本和时间上的挑战。
● 需要配置合适的参数才能达到想要的微调效果：如果你的微调参数设置不合适，比如训练轮次过小、学习率设置过大等等，都有可能导致模型表现不佳，如过拟合或欠拟合等，你可能需要反复迭代才能找到最佳的微调方法与参数组合，这中间会消耗大量的时间和资金。
过拟合（Overfitting） 是机器学习中常见的现象，指的是模型在训练数据上表现非常好，但在测试数据或实际应用中表现很差。就好像一个学生只记住了题目的答案，但却无法理解题目的本质，无法灵活运用知识解决新问题。
欠拟合也是机器学习中常见的现象，指的是由于训练过程过于简单，导致模型在训练数据与测试数据上表现都不好。
总而言之，大模型微调就像给模型进行个性化定制，可以帮助它更好地完成你的任务，但需要你投入时间和精力进行准备和训练。


#### 3.5 如何进行微调

3.5.1 业务决策
你在决定是否在业务领域中使用微调大模型时，可以考虑多个因素以确保采用微调大模型的方法能带来预期的业务价值。
● 业务需求匹配度
首先明确业务的具体需求，明确要通过大模型微调解决的具体业务问题和应用场景。可以先问自己以下问题：
    ‒ 你的任务是否需要复杂的语言理解或生成能力？例如，复杂的自然语言生成、意图识别等任务可能受益于大模型微调。
    ‒ 你的任务是否需要高度特定于某个领域或任务的语言能力？例如，法律文书分析、医学文本理解等领域任务。
    ‒ 当前的模型是否已能满足大部分需求？如果能满足，则可能不需要微调。
    ‒ 是否有具体的业务指标来衡量微调前后效果对比？比如微调后的大模型推送给客户的信息更加准确，从而降低投诉率。
● 数据可用性与质量
微调需要足够的高质量领域特定数据。需要评估当前业务系统中是否能够提取出足够的标注数据用于训练，以及数据的质量、代表性是否满足要求。
● 合规与隐私
业务工作者需要确保使用的数据符合法律法规要求，处理个人数据时遵循隐私保护原则，尤其是GDPR等国际和地区隐私法规。此外，还要关注模型偏见、过拟合、泛化能力不足等潜在风险，以及这些风险对业务可能造成的影响。
● 资源和技术可行性
微调过程需要计算资源和时间成本，包括GPU资源、存储空间以及可能的专家人力成本。需要评估项目预算和资源是否允许进行有效微调。
团队是否具备微调大模型所需的技术能力和经验，或者是否有合适的合作伙伴提供技术支持。
总的来说，需要对微调的业务价值进行ROI分析，即进行成本效益分析，评估微调带来的商业价值是否超过其成本，包括直接经济效益和间接效益，如用户体验提升、品牌形象增强等。

3.5.2 微调的流程
1. 数据准备
‒ 数据收集：收集用于微调模型的数据，例如之前的交互记录、常见问题及回答等。
‒ 数据清洗：清洗这些数据，去除敏感信息，保证数据的质量。
2. 模型选择
‒ 选择适合的预训练大模型。准备一个或多个有使用权限的通用大模型。
3. 模型微调
‒ 使用你收集的数据来微调所选模型。
‒ 标注数据：如果需要，对数据进行标注以支持监督学习。
‒ 微调模型：运行微调程序，调整模型的参数使其更适应你的业务数据。
4. 模型评测
    ‒ 你可以在准备训练集的同时，准备一份与训练集格式一致的评测集，该评测集用来评测微调后模型的效果。如果评测集数据条目较少，你可以直接去观察微调后模型的输出，并与评测集的output进行比较。如果评测集数据条目较多，你可以通过百炼的模型评测功能，查看微调后模型的表现。
3. 模型集成
‒ 编写代码将模型调用集成到现有的业务流程中去。
‒ 设定合理的调用逻辑和流程，如何处理模型的输出，如何处理API调用错误等。
‒ 确保API调用遵守数据保护法规。
‒ 实施适当的身份验证和授权控制。
6. 测试与优化
‒ 在开发和测试环境中测试API调用和模型集成。
‒ 根据测试结果优化模型性能。
7. 模型部署
‒ 在生产环境中部署微调后的模型。
8. 监控与维护
‒ 监控模型的性能和API的健康状况。
‒ 定期重新评估和优化模型以适应新数据和业务变化。
9. 持续迭代
‒ 根据用户反馈和业务需求的变化，继续改进模型和API。
在进行这一切工作时，保持良好的文档习惯也至关重要，这样团队成员可以轻松跟踪项目的进展，新加入的成员也能够快速上手。此外，确保所有与微调和部署模型相关的关键决策都得到适当记录和备份。


#### 3.6 微调的方式

##### 按实现工具/平台分类

|方式|说明|适用场景|
| :---: | :---------: | :---------: |
|公有云平台微调|使用 OpenAI Fine-tuning、百度千帆、阿里百炼等云平台|最简单，无需硬件，适合初学者|
|工具库微调|使用 LLaMA-Factory、torchtune 等工具|无需开发成本，只需配置超参数|
|Transformers 库|使用 HuggingFace Transformers|编写训练代码 |更底层，需要编写训练相关代码|
|PyTorch 实现|从零实现大模型架构进行微调|适合学习原理，开发成本高|
|C++/CUDA 实现|最底层实现，性能最好|高性能推理场景，需要硬件知识|

##### 按参数更新方式分类

1. 全量微调（Full Fine-tuning）

|特点 |说明|
| :---: | :---------: |
|更新范围 |更新模型所有参数|
|计算资源 |需要大量 GPU 显存和计算资源|
|效果 |通常效果最好|
|适用场景 |资源充足、任务与预训练差异大|

2. 参数高效微调（PEFT）
只微调少量参数，大幅降低计算成本 。主要包括：

|方法 |原理 |特点|
| :---: | :---------: | :---------: |
|LoRA |在权重上添加低秩矩阵，冻结原参数 |内存开销小，训练高效，社区流行|
|QLoRA |LoRA + 4bit 量化，进一步降低显存 |单卡可微调超大模型，显存占用减半|
|Adapter Tuning |在 Transformer 中嵌入 Adapter 结构 |只微调新增 Adapter 参数，额外参数约 3.6%|
|Prompt Tuning |在输入层加入可学习的 prompt tokens |实现最简单，固定模型前馈层参数|
|Prefix Tuning |在输入 token 前构造 virtual tokens 作为 Prefix |可学习的"隐式"提示，只更新 Prefix 参数|
|P-Tuning v2 |改进的 Prompt Tuning 方法 |在多层加入可训练参数，效果更好|

##### 按训练目标分类 
 
|方法 |全称 |说明|
| :---: | :---------: | :---------: |
|SFT |监督微调 (Supervised Fine-Tuning) |使用问答数据对模型进行微调，使输出形式和内容更优|
|DPO |直接偏好优化 (Direct Preference Optimization) |使用偏好数据（好结果/差结果）对齐人类价值观|
|RLHF |基于人类反馈的强化学习 |使用奖励模型 +PPO 进行偏好对齐，训练更复杂|
|增量预训练 |Continual Pre-training |在领域数据上继续预训练，适应特定领域|

##### 主流微调方法对比

|方法 |显存占用 |训练速度 |效果 |适用场景|
| :---: | :---: | :---: | :---: | :---: |
|全量微调 |高 |慢 |最好 |资源充足|
|LoRA |中 |快 |接近全量 |中小规模数据|
|QLoRA |低 |快 |接近 LoRA |显存非常有限|
|Prompt Tuning |最低 |最快 |稍弱 |快速原型验证|
|Adapter |低 |快 |接近全量 |多任务场景|

##### 选择建议

|需求场景 |推荐方法 |理由|
| :---: | :---------: | :---------: |
|初学者/无硬件 |公有云平台 |最简单，无需配置环境|
|资源有限 |QLoRA |单卡可微调大模型，显存占用最低|
|追求效果 |全量微调/LoRA |效果最好或接近全量|
|多任务切换 |LoRA |多个适配器可在一个基模型上切换|
|快速验证 |Prompt Tuning |实现最简单，训练最快|
|企业生产 |LoRA/QLoRA + SFT/DPO |平衡效果与成本|

##### 总结

|维度 |主要方法|
| :---: | :---------: |
|实现工具 |云平台、LLaMA-Factory、Transformers、PyTorch|
|参数更新 |全量微调、LoRA、QLoRA、Adapter、Prompt|
|训练目标 |SFT（监督微调）、DPO（偏好优化）、RLHF|
|趋势 |PEFT 技术成为主流，LoRA/QLoRA 最流行|

对于大多数场景，LoRA/QLoRA + SFT 是性价比最高的选择，既能保证效果，又能大幅降低训练成本。


### 4、借助 Agent 让大模型应用思考、决策并执行任务

AI Agent（智能体） 是一种能够感知环境、进行推理、做出决策并执行动作的智能系统。与传统大模型应用相比，Agent 不仅仅是 "回答问题"，而是能够主动完成复杂任务。

Agent = LLM + 工具 + 记忆 + 规划，从"回答问题"升级为"完成任务"。


#### Agent 的典型架构
```
┌─────────────────────────────────────────────────────────┐
│                      用户输入                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    感知层 (Perception)                   │
│  • 理解用户意图  • 解析上下文  • 提取关键信息                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    规划层 (Planning)                     │
│  • 任务拆解  • 步骤规划  • 依赖关系分析                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    决策层 (Decision)                     │
│  • 工具选择  • 参数确定  • 执行顺序                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    执行层 (Action)                       │
│  • 调用工具/API  • 执行代码  • 读写数据                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    记忆层 (Memory)                       │
│  • 短期记忆 (对话上下文)  • 长期记忆 (知识库)                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                      输出结果                            │
└─────────────────────────────────────────────────────────┘
```


#### 主流 Agent 框架

|框架|特点|适用场景|
| :---: | :---------: | :---------: |
|LangChain|生态丰富，组件齐全|通用 Agent 开发|
|AutoGen|多 Agent 协作能力强|复杂任务协同|
|LlamaIndex|数据检索增强|RAG + Agent|
|CrewAI|角色化 Agent 设计|团队式任务执行|
|Dify|可视化编排|快速原型开发|


## 二、大模型部署

### 1、GPU

|特性|T4|V100|A10|A100|H100|L20 (中国特供)|H20 (中国特供)|
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
|发布年份|2018|2017|2021|2020|2022|2023|2024|
|核心架构|Turing|Volta|Ampere|Ampere|Hopper|Ada Lovelace|Hopper|
|工艺制程|12nm|12nm|8nm|7nm|4nm|5nm|4nm|
|显存容量|16 GB|16/32 GB|24 GB|40/80 GB|80 GB|48 GB|96 GB|
|显存类型|GDDR6|HBM2|GDDR6|HBM2e|HBM3|GDDR6|HBM3|
|显存带宽|320 GB/s|900 GB/s|600 GB/s|1.5~2.0 TB/s|3.35 TB/s|864 GB/s|4.0 TB/s|
|FP16 算力|65 TFLOPS|125 TFLOPS|125 TFLOPS|312 TFLOPS|~1,979 TFLOPS*|~119 TFLOPS*|~148 TFLOPS*|
|BF16 支持|❌ 不支持|⚠️ 弱支持|✅ 支持|✅ 支持|✅ 原生加速|✅ 支持|✅ 支持|
|FP8 支持|❌ 不支持|❌ 不支持|❌ 不支持|❌ 不支持|✅ Transformer引擎|⚠️ 有限支持|⚠️ 被严重阉割|
|互联带宽|PCIe 3.0|NVLink 2.0|PCIe 4.0|NVLink 3.0|NVLink 4.0|PCIe 5.0|NVLink (受限)|
|主要定位|入门推理/转码|旧款训练旗舰|图形+AI混合|通用训练/推理|全球训练旗舰|中国推理主力|中国训练替代|
|大模型训练|❌ 不可用|⚠️ 仅限小模型微调|⚠️ 仅限小模型微调|✅ 主流选择 (80G)|✅ 最强王者|⚠️ 仅限微调/LoRA|✅ 靠堆数量集群训练|
|大模型推理|✅ 小模型 (7B Int4)|✅ 中小模型|✅ 中等模型 (7-14B)|✅ 大模型 (30-70B)|✅ 超大并发/大模型|✅ 高性价比 (30-50B)|✅ 大显存优势 (70B+)|
|国内合规性|✅ 可买|✅ 可买 (二手/存量)|✅ 可买|❌ 禁售|❌ 禁售|✅ 合规在售|✅ 合规在售|
|典型单卡价格|$ (~低价)|$$ (二手波动)|$$|$$$ (黑市极高)|$$$$ (海外$3万+)|$$ (中等)|$$$ (较高)|


### 2、基础环境

#### 安装 CUDA
```shell
# 1. 下载 CUDA 安装包
# 访问 https://developer.nvidia.com/cuda-toolkit-archive 选择对应版本
wget https://developer.download.nvidia.com/compute/cuda/12.1.1/local_installers/cuda_12.1.1_530.30.02_linux.run

# 2. 添加执行权限
sudo chmod +x cuda_12.1.1_530.30.02_linux.run

# 3. 运行安装（交互式）
sudo ./cuda_12.1.1_530.30.02_linux.run

# 添加 CUDA 到 PATH
echo 'export PATH=/usr/local/cuda/bin:$PATH' | sudo tee /etc/profile.d/cuda.sh
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' | sudo tee -a /etc/profile.d/cuda.sh

# 使配置生效
source /etc/profile.d/cuda.sh

# 添加环境变量到 Bash 环境
cat >> ~/.bashrc << 'EOF'

# CUDA 12.1 环境变量
export PATH=/usr/local/cuda-12.1/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH
EOF

# 保存退出 vim 后，执行：
source ~/.bashrc

# 验证 CUDA 安装成功
nvcc --version
```

#### 更新 Python3
```shell
# 安装python3.11
sudo yum install -y python3.11
sudo yum install -y python3.11-pip
sudo yum install -y python3.11-devel gcc gcc-c++

# 备份原 pip3
sudo mv /usr/bin/pip3 /usr/bin/pip3.bak
# 创建新软链接
sudo ln -s /usr/bin/pip3.11 /usr/bin/pip3
# 验证
pip3 --version

# 备份原 python3
sudo mv /usr/bin/python3 /usr/bin/python3.bak
# 创建新软链接
sudo ln -s /usr/bin/python3.11 /usr/bin/python3
# 验证
python3 --version

# 使用 venv 模块创建隔离的 Python 环境
python3.11 -m venv .venv
source .venv/bin/activate
# 退出
deactivate
# venv 环境异常
rm -rf .venv 
```

#### PyTorch
- 安装 
```shell
# 根据 nvidia-smi 显示的 CUDA 版本选择对应的 PyTorch
# CUDA 12.1
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# CUDA 11.8
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
# CUDA 11.7
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
# ALIYUN 的源
pip3 install torch torchvision torchaudio --index-url http://mirrors.cloud.aliyuncs.com/pypi/simple/
```

- 验证脚本
```python
# 验证 PyTorch
import torch

# 打印版本
print("PyTorch 版本：", torch.__version__)

# 检查 CUDA 是否可用
print("CUDA 可用：", torch.cuda.is_available())

# 如果 CUDA 可用，显示显卡信息
if torch.cuda.is_available():
    print("GPU 数量：", torch.cuda.device_count())
    print("GPU 名称：", torch.cuda.get_device_name(0))
```


#### 其他依赖库

- 安装 CUDNN、NCCL
```shell
# 下载安装 cuDNN 9.0 for CUDA 12.x
wget https://developer.download.nvidia.com/compute/cudnn/9.0.0/local_installers/cudnn-local-repo-rhel8-9.0.0-1.0-1.x86_64.rpm

# RPM 包安装（CentOS/RHEL）
# cudnn https://developer.nvidia.com/cudnn-downloads?target_os=Linux&target_arch=x86_64&Distribution=RHEL&target_version=8&target_type=rpm_network&Configuration=Full
sudo rpm -ivh cudnn-local-repo-rhel8-9.0.0-1.0-1.x86_64.rpm
sudo cp /var/log/cudnn-local-repo-rhel8-9.0.0-1.0-1/*.key /etc/pki/rpm-gpg/
sudo yum install cudnn
yum install cudnn libcudnn9 libcudnn9-devel
yum install -y libnccl libnccl-devel
ldconfig -p | grep nccl
```

- 验证
```shell
# 单条验证命令
python3 -c "import torch; print('CUDA:', torch.cuda.is_available(), 'cuDNN:', torch.backends.cudnn.is_available(), 'cuDNN ver:', torch.backends.cudnn.version())"
```


### 3、运行模型
- 模型下载
```python
# 模型下载
from modelscope import snapshot_download

model_dir = snapshot_download('Qwen/Qwen3-8B', cache_dir='/root/autodl-tmp', revision='master')
# model_dir = snapshot_download('deepseek-ai/deepseek-llm-7b-chat', cache_dir='/root/autodl-tmp', revision='master')
```

- [Qwen3-8B vLLM 部署调用](https://github.com/datawhalechina/self-llm/blob/master/models/Qwen3/02-Qwen3-8B-vLLM%20%E9%83%A8%E7%BD%B2%E8%B0%83%E7%94%A8.md)
```shell
# 安装 modelscope 和 vllm
python -m pip install --upgrade pip
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install modelscope
pip install vllm

# 模型下载
modelscope download --model Qwen/Qwen3-8B  --local_dir /root/autodl-tmp/Qwen/Qwen3-8B 

# Qwen3-8B 兼容 OpenAI API 协议，所以我们可以直接使用 vLLM 创建 OpenAI API 服务器。vLLM 部署实现 OpenAI API 协议的服务器非常方便。默认会在 http://localhost:8000 启动服务器。服务器当前一次托管一个模型，并实现列表模型、completions 和 chat completions 端口。
# completions：是基本的文本生成任务，模型会在给定的提示后生成一段文本。这种类型的任务通常用于生成文章、故事、邮件等。
# chat completions：是面向对话的任务，模型需要理解和生成对话。这种类型的任务通常用于构建聊天机器人或者对话系统。
# 在创建服务器时，可以指定模型名称、模型路径、聊天模板等参数。
# --help=all 获取所有参数
# --host 和 --port 参数指定地址。
# --model 参数指定模型名称。
# --chat-template 参数指定聊天模板。
# --served-model-name 指定服务模型的名称。
# --max_model_len 指定模型的最大长度。
# --enable-reasoning 开启思考模式
# --reasoning-parser 指定如何解析模型生成的推理内容。设置 --enable-reasoning 参数时，--reasoning-parser 是必需的。推理模型会在输出中包含一个额外的 reasoning_content 字段，该字段包含导致最终结论的推理步骤。通过指定合适的解析器，可以正确提取和格式化这些推理内容。例如 deepseek_r1 解析器适用于 DeepSeek R1 系列模型，能够解析 ... 格式的内容
VLLM_USE_MODELSCOPE=true vllm serve /root/autodl-tmp/Qwen/Qwen3-8B --host 127.0.0.1 --port 8001 --served-model-name Qwen3-8B --max_model_len 40960 --enable-reasoning --reasoning-parser deepseek_r1

# Qwen3-8B 模型运行
python -m vllm.entrypoints.openai.api_server \
--model /root/autodl-tmp/Qwen/Qwen3-8B \
--served-model-name Qwen3-8B \
--trust-remote-code \
--dtype float16

# Qwen3-8B 模型调用
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-8B",
    "messages": [
      {"role": "user", "content": "你好, 你是谁, 介绍下LLM."}
    ],
    "max_tokens": 4096
  }'
```


## 三、大模型相关文档

- [阿里云大模型工程师ACA认证课程](https://edu.aliyun.com/course/3126500/)

- [千问的github主页](https://github.com/QwenLM/Qwen/blob/main/README_CN.md)

- [LLaMA Factory v0.9 中文文档](https://www.bookstack.cn/read/llama-factory-0.9-zh/df325ab5f5e04d35.md)

- [开源大模型食用指南](https://github.com/datawhalechina/self-llm)
- [Happy-LLM 从零开始的大语言模型原理与实践教程](https://github.com/datawhalechina/happy-llm)


- [vLLM](https://docs.vllm.com.cn/en/latest/)

- [inference-nv-pytorch](https://help.aliyun.com/zh/cs/user-guide/inference-nv-pytorch-25-11)

- 模型
https://modelscope.cn/models/openai-community/openai-gpt
https://modelscope.cn/models/laonansheng/ruanqing-Z-Image-Turbo-Tongyi-MAI-v1.0
https://docs.vllm.ai/projects/llm-compressor/en/0.7.0/
https://modelscope.cn/organization/qwen
https://github.com/chaitin/PandaWiki


- 业界有成熟的评测工具如Ragas https://docs.ragas.io/en/stable/concepts/metrics/index.html#

- [OpenClaw](https://bailian.console.aliyun.com/cn-beijing/?spm=5176.29597918.J_zK-KF2dfzE2iOekxSO0K-.1.63d37ca08xls0G&tab=doc#/doc/?type=model&url=3020785)

- 书
	- 大模型微调