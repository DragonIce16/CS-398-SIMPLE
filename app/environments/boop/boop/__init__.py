from gym.envs.registration import register

register(
    id='Boop-v0',
    entry_point='boop.envs:BoopEnv',
)


