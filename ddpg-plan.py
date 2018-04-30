import logging
from agent import *
from component import *
from utils import *
from model import *
import matplotlib.pyplot as plt

def ddpg_continuous(game, log_dir=None):
    config = Config()
    if log_dir is None:
        log_dir = get_default_log_dir(ddpg_continuous.__name__)
    config.task_fn = lambda: Roboschool(game)
    config.evaluation_env = Roboschool(game, log_dir=log_dir)
    config.actor_network_fn = lambda state_dim, action_dim: DeterministicActorNet(
        action_dim, FCBody(state_dim, (300, 200), gate=F.tanh))
    config.critic_network_fn = lambda state_dim, action_dim: DeterministicCriticNet(
        TwoLayerFCBodyWithAction(state_dim, action_dim, [400, 300], gate=F.tanh))
    config.actor_optimizer_fn = lambda params: torch.optim.Adam(params, lr=1e-4)
    config.critic_optimizer_fn = lambda params: torch.optim.Adam(params, lr=1e-3)
    config.replay_fn = lambda: Replay(memory_size=1000000, batch_size=64)
    config.discount = 0.99
    config.state_normalizer = RunningStatsNormalizer()
    config.max_steps = 1e6
    config.random_process_fn = lambda action_dim: GaussianProcess(
        action_dim, LinearSchedule(0.3, 0, 1e6))

    config.min_memory_size = 64
    config.target_network_mix = 1e-3
    config.logger = Logger('./log', logger)
    run_episodes(DDPGAgent(config))


def ddpg_plan_continuous(game, log_dir=None, **kwargs):
    config = Config()
    if log_dir is None:
        log_dir = get_default_log_dir(ddpg_plan_continuous.__name__)
    config.task_fn = lambda: Roboschool(game)
    config.evaluation_env = Roboschool(game, log_dir=log_dir)
    config.network_fn = lambda state_dim, action_dim: SharedDeterministicNet(
        state_dim, action_dim, config.discount, gate=F.tanh, detach_action=kwargs['detach_action']
    )
    config.optimizer_fn = lambda params: torch.optim.Adam(params, lr=1e-4)
    config.replay_fn = lambda: Replay(memory_size=1000000, batch_size=64)
    config.discount = 0.99
    config.state_normalizer = RunningStatsNormalizer()
    config.max_steps = 1e6
    config.random_process_fn = lambda action_dim: GaussianProcess(
        action_dim, LinearSchedule(0.3, 0, 1e6))

    config.min_memory_size = 64
    config.target_network_mix = 1e-3
    config.value_loss_weight = 10.0
    config.lam = kwargs['lam']
    config.logger = Logger('./log', logger)
    run_episodes(PlanDDPGAgent(config))

def multi_runs(game, fn, tag, **kwargs):
    mkdir('./log/%s' % (game))
    mkdir('./log/%s/%s' % (game, fn.__name__))
    runs = np.arange(0, 5)
    for run in runs:
        log_dir = './log/%s/%s/%s-run-%d' % (game, fn.__name__, tag, run)
        fn(game, log_dir, **kwargs)

def plot(**kwargs):
    import matplotlib.pyplot as plt
    figure = kwargs['figure']
    del kwargs['figure']
    plotter = Plotter()
    names = plotter.load_log_dirs(**kwargs)
    data = plotter.load_results(names, episode_window=100)

    plt.figure(figure)
    for i, name in enumerate(names):
        x, y = data[i]
        plt.plot(x, y, color=Plotter.COLORS[i], label=name if i==0 else '')
    plt.legend()
    plt.ylim([-100, 1400])
    plt.xlabel('timesteps')
    plt.ylabel('episode return')
    # plt.show()

if __name__ == '__main__':
    mkdir('data')
    mkdir('data/video')
    mkdir('dataset')
    mkdir('log')
    os.system('export OMP_NUM_THREADS=1')
    os.system('export MKL_NUM_THREADS=1')
    torch.set_num_threads(1)
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)

    # game = 'RoboschoolHopper-v1'
    game = 'RoboschoolAnt-v1'
    # multi_runs(game, ddpg_continuous, tag='ddpg')
    # multi_runs(game, ddpg_plan_continuous, tag='ddpg_plan')

    # multi_runs(game, ddpg_plan_continuous, tag='ddpg_plan_lam_1.0',
    #            lam=LinearSchedule(1.0, 1.0, 1e6), detach_action=False)
    # multi_runs(game, ddpg_plan_continuous, tag='ddpg_plan_lam_1.0_to_0',
    #            lam=LinearSchedule(1.0, 0, 1e6), detach_action=False)
    # multi_runs(game, ddpg_plan_continuous, tag='ddpg_plan_lam_1.0_to_0_fast',
    #            lam=LinearSchedule(1.0, 0, 5e5), detach_action=False)
    # multi_runs(game, ddpg_plan_continuous, tag='ddpg_plan_lam_0_no_action',
    #            lam=LinearSchedule(0, 0, 5e5), detach_action=True)

    # plot(pattern='.*Hopper.*ddpg_continuous.*', figure=0)
    # plot(pattern='.*Hopper.*ddpg_plan_continuous.*', figure=1)

    # plot(pattern='.*Ant.*ddpg_continuous.*')
    # plot(pattern='.*Ant.*ddpg_plan_continuous.*')
    # plt.show()

