import torch
import numpy as np
import pandas as pd
from config import get_config
from core.environment.env import DroneSwarmSearch


class RLAgent:
    def __init__(self, env, y, lr, episodes, drones_initial_positions):
        self.env = env
        self.y = y
        self.lr = lr
        self.episodes = episodes
        self.drones_initial_positions = drones_initial_positions

        self.num_agents = len(env.possible_agents)
        self.num_obs = (
                2 * self.num_agents
                + env.observation_space("drone0").nvec[0]
                * env.observation_space("drone0").nvec[1]
        )
        self.num_actions = len(env.action_space("drone0"))

    def flatten_state(self, observations):
        flatten_all = []

        for drone_index in range(self.num_agents):
            drone_position = torch.tensor(
                observations["drone" + str(drone_index)]["observation"][0]
            )
            flatten_obs = torch.flatten(
                torch.tensor(observations["drone" + str(drone_index)]["observation"][1])
            )
            others_position = torch.flatten(
                torch.tensor(
                    [
                        observations["drone" + str(index)]["observation"][0]
                        for index in range(self.num_agents)
                        if index != drone_index
                    ]
                )
            )

            flatten_all.append(
                torch.cat((drone_position, others_position, flatten_obs), dim=-1)
            )

        return flatten_all

    def enhance_reward(self, drone_position, probability_matrix, action):
        if action in {0, 1, 2, 3} and (drone_position[0] >= 0 and drone_position[0] < len(probability_matrix)) and (
                drone_position[1] >= 0 and drone_position[1] < len(probability_matrix[0])):
            match action:
                case 0:  # LEFT
                    previous_position = (drone_position[0] + 1, drone_position[1])
                case 1:  # RIGHT
                    previous_position = (drone_position[0] - 1, drone_position[1])

                case 2:  # UP
                    previous_position = (drone_position[0], drone_position[1] + 1)
                case 3:  # DOWN
                    previous_position = (drone_position[0], drone_position[1] - 1)

            previous_probability = probability_matrix[previous_position[0]][
                previous_position[1]
            ]
            current_probability = probability_matrix[drone_position[0]][
                drone_position[1]
            ]

            if current_probability > previous_probability:
                return 500

            return -500

        return 0

    def get_reward_enhanced(self, observations, actions_dict, current_reward):
        reward = current_reward["total_reward"]
        new_rewards = {}

        for drone, action in actions_dict.items():
            drone_position = observations[drone]["observation"][0]
            probability_matrix = observations[drone]["observation"][1]
            new_reward = self.enhance_reward(drone_position, probability_matrix, action)
            new_rewards[drone] = new_reward if new_reward != 0 else current_reward[drone]
            reward += new_reward if new_reward != 0 else 0

        new_rewards["total_reward"] = reward
        return reward, new_rewards

    def get_random_speed_vector(self):
        """Returns a random speed vector for the environment, from -0.5 to 0.5, 0.1 step"""
        return [
            round(np.random.uniform(-0.1, 0.1), 1),
            round(np.random.uniform(-0.1, 0.1), 1),
        ]

    def train(self):
        nn = torch.nn.Sequential(
            torch.nn.Linear(self.num_obs, 512),
            torch.nn.ReLU(),
            torch.nn.Linear(512, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, self.num_actions),
            torch.nn.Softmax(dim=-1),
        )
        optim = torch.optim.Adam(nn.parameters(), lr=self.lr)
        statistics, show_rewards, show_actions, all_rewards = [], [], [], []

        nn = nn.float()
        stop = False

        for i in range(self.episodes + 1):
            if stop:
                break

            vector = self.get_random_speed_vector()
            state = self.env.reset(
                drones_positions=self.drones_initial_positions, vector=vector
            )
            obs_list = self.flatten_state(state)
            done = False
            actions, states, rewards = [], [], []
            count_actions, total_reward = 0, 0

            while not done:
                episode_actions = {}

                for drone_index in range(self.num_agents):
                    probs = nn(obs_list[drone_index].float())
                    dist = torch.distributions.Categorical(probs)
                    episode_actions[f"drone{drone_index}"] = dist.sample().item()

                obs_list_, reward_dict, _, done, _ = self.env.step(episode_actions)

                reward, reward_dict = self.get_reward_enhanced(
                    obs_list_, episode_actions, reward_dict
                )

                actions.append(
                    torch.tensor(list(episode_actions.values()), dtype=torch.int)
                )

                states.append(obs_list)
                rewards.append(
                    [
                        drone_reward
                        for key, drone_reward in reward_dict.items()
                        if "drone" in key
                    ]
                )

                obs_list = self.flatten_state(obs_list_)
                count_actions += self.num_agents
                total_reward += reward
                done = any(done.values())

            show_rewards.append(total_reward)
            all_rewards.append(total_reward)
            show_actions.append(count_actions)

            if len(all_rewards) > 100:
                if all([r >= 100000 for r in all_rewards[-20:]]):
                    stop = True
                    print("Acabou mais cedo")

            if i % 100 == 0:
                print(
                    f"Up to episode = {i}, Actions (mean) = {sum(show_actions)/ len(show_actions)}, "
                    f"Reward (mean) = {sum(show_rewards) / len(show_rewards)}"
                )

                show_rewards, show_actions = [], []

            statistics.append([i, count_actions, total_reward])

            discounted_returns = []
            for t in range(len(rewards)):
                G_list = []

                for drone_index in range(self.num_agents):
                    agent_rewards = [r[drone_index] for r in rewards]
                    G_list.append(
                        sum(
                            (self.y ** k) * r
                            for k, r in enumerate(agent_rewards[t:])
                        )
                    )

                discounted_returns.append(G_list)

            for state_list, action_list, G_list in zip(
                    states, actions, discounted_returns
            ):
                for drone_index in range(self.num_agents):
                    probs = nn(state_list[drone_index].float())
                    dist = torch.distributions.Categorical(probs=probs)
                    log_prob = dist.log_prob(action_list[drone_index])

                    loss = -log_prob * G_list[drone_index]

                    optim.zero_grad()
                    loss.backward()
                    optim.step()


        return nn, statistics


config = get_config(1)

env = DroneSwarmSearch(
    grid_size=config.grid_size,
    render_mode="ansi",
    render_grid=False,
    render_gradient=False,
    n_drones=config.n_drones,
    person_initial_position=config.person_initial_position,
    disperse_constant=config.disperse_constant,
    timestep_limit=100,
)

rl_agent = RLAgent(
    env,
    y=0.999999,
    lr=0.00002,
    episodes=20_000,
    drones_initial_positions=config.drones_initial_positions,
)
nn, statistics = rl_agent.train()

torch.save(nn, f"data/nn_{config.grid_size}_{config.grid_size}_{config.n_drones}.pt")
df = pd.DataFrame(statistics, columns=["episode", "actions", "rewards"])
df.to_csv(f"data/statistics_{config.grid_size}_{config.grid_size}_{config.n_drones}.csv", index=False)
