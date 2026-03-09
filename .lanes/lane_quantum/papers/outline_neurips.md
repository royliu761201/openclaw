## Abstract

### Core Problem and Proposed Solution
The abstract will introduce the challenge of non-stationarity in multi-agent systems (MAS) and how it hinders traditional reinforcement learning approaches. It will then briefly present our novel framework that leverages active inference for principled communication, enabling agents to adapt to changing environments and other agents' behaviors.
(200 words)

### Key Contributions and Impact
This section will succinctly list the main contributions, such as a new active inference formulation for MAS communication and empirical validation demonstrating improved performance in non-stationary settings.
(150 words)

## 1. Introduction

### 1.1 The Challenge of Non-Stationarity in Multi-Agent Systems
This subsection will elaborate on the difficulties posed by non-stationarity in MAS, where the environment dynamics and other agents' policies change over time. This leads to convergence issues and suboptimal performance for standard MARL algorithms.
(300 words)
[cite: Foerster et al., 2017]

### 1.2 Communication as a Solution for Adaptation
We will discuss how explicit communication can help agents infer and adapt to non-stationarity. This involves sharing information about internal states, beliefs, or intentions, thereby mitigating the negative effects of changing environments and agent policies.
(300 words)
[cite: Sunehag et al., 2017]

### 1.3 Active Inference for Principled Communication
This subsection introduces active inference as a unifying framework for perception, action, and learning. We will highlight its potential to provide a principled approach to communication by framing it as an active process of minimizing prediction error and maximizing information gain, particularly in non-stationary settings.
(400 words)
[cite: Friston, 2010; Chua et al., 2018]

### 1.4 Our Approach and Contributions
A clear statement of our proposed method and its key contributions will be presented. This will include a brief overview of how active inference is adapted for MAS communication and the specific benefits (e.g., robustness, interpretability) it offers.
(250 words)

## 2. Related Work

### 2.1 Multi-Agent Reinforcement Learning and Non-Stationarity
This section will review existing approaches to MARL, focusing on methods that attempt to address non-stationarity, such as mean-field approximations, opponent modeling, and centralized training with decentralized execution. We will highlight their limitations in truly dynamic environments.
(300 words)
[cite: Lowe et al., 2017; Tampubolon et al., 2020]

### 2.2 Communication in Multi-Agent Systems
A survey of current communication protocols in MAS, including learned communication (e.g., CommNet, DIAL) and structured communication. We will discuss how these approaches handle information exchange and their applicability to non-stationary scenarios.
(300 words)
[cite: Sukhbaatar et al., 2016; Lazaridou et al., 2018]

### 2.3 Active Inference and its Applications
This subsection will provide a background on active inference, its core principles (e.g., free energy minimization, variational Bayesian inference), and its successful applications in single-agent settings, particularly in cognitive science and robotics.
(250 words)
[cite: Solovey et al., 2016]

### 2.4 Bridging Communication and Active Inference for MAS
This section will critically analyze the nascent efforts to combine active inference with multi-agent systems and communication, identifying the gaps our work aims to fill.
(200 words)

## 3. Method: Principled Communication via Active Inference

### 3.1 Active Inference for Individual Agents
We will detail the core active inference formulation for a single agent. This includes defining the agent's generative model of the world and other agents, its beliefs about hidden states, and the free energy minimization objective for perception and action.
(400 words)
[cite: Friston, 2010]

### 3.2 Communication as Information Exchange under Active Inference
This subsection will introduce our novel extension to the active inference framework for communication. We will define communication actions as a specific type of action that intentionally conveys information to other agents to reduce their prediction errors and facilitate joint goal achievement. This will involve defining a joint generative model across agents.
(500 words)

### 3.3 Learning Communication Policies
We will describe how communication policies are learned within the active inference framework. This might involve variational inference over communication actions or a separate learning process guided by the overall free energy minimization objective. The focus will be on learning to communicate effectively in response to observed non-stationarity.
(400 words)

### 3.4 Handling Non-Stationarity
This subsection will explicitly detail how our active inference formulation accounts for non-stationarity. This will involve agents updating their beliefs about the environmental dynamics and other agents' policies based on incoming communication and sensory data. The ability to adapt the generative model dynamically will be emphasized.
(400 words)

## 4. Experiments

### 4.1 Experimental Setup and Environments
We will describe the chosen multi-agent environments, emphasizing those with inherent non-stationarity (e.g., predator-prey scenarios with evolving prey behavior, coordination tasks with changing agent roles). We will detail the state and action spaces, reward structures, and the specific non-stationarity mechanisms.
(300 words)

### 4.2 Baselines and Evaluation Metrics
This subsection will list the state-of-the-art MARL and communication algorithms used as baselines. We will define the key performance metrics, focusing on convergence speed, final performance, robustness to non-stationarity, and potentially measures of communication efficiency and interpretability.
(250 words)

### 4.3 Results and Analysis
Detailed presentation of experimental results. This will include quantitative comparisons against baselines, ablation studies to demonstrate the importance of specific components of our method (e.g., communication, active inference aspects), and qualitative analyses of learned communication patterns.
(600 words)

### 4.4 Impact of Non-Stationarity on Communication
Analysis of how varying degrees of non-stationarity affect the learned communication strategies and overall system performance. This will highlight the adaptive capabilities of our proposed method.
(300 words)

## 5. Conclusion and Future Work

### 5.1 Summary of Contributions
A concise summary of the paper's main findings and contributions, reiterating the effectiveness of principled communication via active inference for non-stationary MAS.
(150 words)

### 5.2 Limitations and Future Directions
Discussion of the current limitations of our approach (e.g., scalability, computational complexity) and outlining promising avenues for future research, such as extending to more complex coordination tasks, exploring different forms of communication, or applying to real-world robotic systems.
(250 words)