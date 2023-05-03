# Drone Swarm Search

## About:

The Drone Swarm Search project is an environment, based on PettingZoo, that is to be used in conjunction with multi-agent (or single-agent) reinforcement learning algorithms. It is an environment in which the agents (drones), have to find the targets (shipwrecked people). The agents do not know the position of the target, and do not receive rewards related to their own distance to the target(s). However, the agents receive the probabilities of the target(s) being in a certain cell of the map. The aim of this project is to aid in the study of reinforcement learning algorithms that require dynamic probabilities as inputs. A visual representation of the environment is displayed below. To test the environment (without an algorithm), run `basic_env.py`.

### Visualization example:

<p align="center">
    <img src="https://github.com/PFE-Embraer/drone-swarm-search/blob/env-cleanup/docs/gifs/render_with_grid_gradient.gif" width="400" height="400" align="center">
</p>

The following code was used in order to create the representation above:

```python
from core.environment.env import DroneSwarmSearch

env = DroneSwarmSearch(
    grid_size=50, 
    render_mode="human", 
    render_grid = True,
    render_gradient = True,
    n_drones=11, 
    vector=[0.5, 0.5],
    person_initial_position = [5, 10],
    disperse_constant = 3)

def policy(obs, agent):
    actions = {}
    for i in range(11):
        actions["drone{}".format(i)] = 1
    return actions


observations = env.reset()
rewards = 0
done = False

while not done:
    actions = policy(observations, env.get_agents())
    observations, reward, _, done, info = env.step(actions)
    rewards += reward["total_reward"]
    done = True if True in [e for e in done.values()] else False

print(rewards)
```

### Installing Dependencies

Using Python version above or equal to 3.10.5.

In order to use the environment download the dependencies using the following command `pip install -r requirements.txt`.

### General Info
| Import            | from core.environment.env import DroneSwarmSearch  |
| -------------     | -------------                                      |
| Action Space      | Discrete (5)                                       |
| Action Values     | [0,1,2,3,4,5]                                      |  
| Agents            | N                                                  |
| Observation Space | {droneN: {observation: ((x, y), probability_matrix}|

### Action Space
| Value         | Meaning       |
| ------------- | ------------- |
| 0             | Move Left     |
| 1             | Move Right    |
| 2             | Move Up       |
| 3             | Move Down     |
| 4             | Search Cell   |
| 5             | Idle          |

### Inputs
| Inputs                    | Possible Values       |
| -------------             | -------------         |
| `grid_size`               | `int(N)`              |
| `render_mode`             | `"ansi" or "human"`   |  
| `render_grid`             | `bool`                |
| `render_gradient`         | `bool`                |
| `n_drones`                | `int(N)`              |
| `vector`                  | `[float(x), float(y)` |
| `person_initial_position` | `[int(x), int(y)]`    |
| `disperse_constant`       | `float`               |

### `grid_size`:

The grid size defines the area in which the search will happen. It should always be an integer greater than one.

### `render_mode`:

There are two available render modes, *ansi*  and *human*.

**Ansi**: This mode presents no visualization and is intended to train the reinforcement learning algorithm.

**Human**: This mode presents a visualization of the drones actively searching the target, as well as the visualization of the person moving according to the input vector. 

### `render_grid`:

The *render_grid* variable is a simple boolean that if set to **True** along with the `render_mode = “human”` the visualization will be rendered with a grid, if it is set to **False** there will be no grid when rendering.   

### `render_gradient`:

### `n_drones`:

### `vector`:

### `person_initial_position`:

### `disperse_constant`:



