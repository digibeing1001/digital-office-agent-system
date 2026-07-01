# rl-benchmark — RL 实验标配

## 用途
强化学习实验的标准化工具链。基于 Stable-Baselines3(SB3)实现常用算法(PPO/SAC/TD3),从 RL Baselines3 Zoo 加载调好的超参,避免从零实现算法,结果与 OpenRLBenchmark 对标。

## 触发条件
- 需要训练或评估强化学习智能体时。
- 用户提到"强化学习""PPO""SAC""RL 实验"时。
- 需要和社区 benchmark 对比 RL 性能时。

## 工具依赖
```bash
pip install stable-baselines3[extra] gymnasium
# RL Baselines3 Zoo(调好的超参仓库)
git clone https://github.com/DLR-RM/rl-baselines3-zoo.git
```

## 操作步骤
1. 根据任务类型选算法:离散动作用 PPO/DQN,连续动作用 SAC/TD3。
2. 从 RL Baselines3 Zoo 的 `hyperparameters/` 加载对应算法的调好的超参。
3. 用 SB3 创建模型并训练。
4. 训练后用 `evaluate_policy` 评估。
5. 记录到 MLflow,与 OpenRLBenchmark 的同环境结果对比。

## 调用示例
```python
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.vec_env import VecMonitor, DummyVecEnv
import gymnasium as gym
import mlflow

def make_env():
    env = gym.make("CartPole-v1")
    return env

env = DummyVecEnv([make_env])
env = VecMonitor(env)

# 加载 Zoo 调好的超参(此处简化,实际从 yaml 读)
hyperparams = {"learning_rate": 2.5e-4, "n_steps": 128,
               "batch_size": 256, "n_epochs": 10, "gamma": 0.99}

with mlflow.start_run():
    mlflow.log_params(hyperparams)
    mlflow.set_tag("algo", "PPO")
    mlflow.set_tag("env", "CartPole-v1")

    model = PPO("MlpPolicy", env, verbose=1, **hyperparams)
    model.learn(total_timesteps=100_000)

    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=20)
    mlflow.log_metric("mean_reward", mean_reward)
    mlflow.log_metric("std_reward", std_reward)
    print(f"mean={mean_reward:.2f} +/- {std_reward:.2f}")

    model.save("ppo_cartpole.zip")
```

## 输出格式
- 训练好的模型文件(`.zip`)。
- 评估指标:mean_reward、std_reward。
- MLflow run 记录,含算法、环境、超参 tag。

## 约束
- 不自己实现 RL 算法,统一用 SB3。
- 超参优先从 RL Baselines3 Zoo 加载,不凭感觉手调。
- 评估必须用固定 seed 的 `evaluate_policy`,报告均值和标准差。
- 结果需与 OpenRLBenchmark 同环境同算法的结果对比,偏差过大需排查。
