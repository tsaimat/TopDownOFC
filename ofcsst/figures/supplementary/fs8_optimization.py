from dataclasses import replace

from ofcsst import simulation
from ofcsst.utils import ids, keys, paths, constants
from ofcsst.figures import helper
from ofcsst.figures.main.f3efg_ofc_sst import (
    OFC_SIM,
    NO_OFC_SIM,
    final_simulation,
    plot_expert_time,
    FigureConfig,
)
from ofcsst.figures.main.f3efg_ofc_sst import (
    plot_performance_bars,
    plot_cumulative_distribution,
)
from ofcsst.figures.main.f3efg_ofc_sst import COLOR_NO_OFC, COLOR_WT, SAVE_PATH

TASK_ID = ids.BINARY_2VN
PLOT_DIR = paths.SUPPLEMENTARY_FIG_DIR / "figs8"
DB_PATH = paths.SUPPLEMENTARY_SIMULATION_DIR / "fig_s8_optimization.db"
COLORS = [(114 / 255.0, 146 / 255.0, 179 / 255.0), helper.COLOR_GAIN]

# Control algorithms optimised for reversal learning (see scan_control_algorithms)
CONTROL_SIMS = (
    ids.SIM_CONVEX_NO_GAIN_DEEP_PG,
    ids.SIM_CONVEX_NO_GAIN_DEEP_Q,
    ids.SIM_CONVEX_PURE_PG_GAIN,
    ids.SIM_CONVEX_PURE_Q_GAIN,
    ids.SIM_CONVEX_RW,
)
CONTROL_LABELS = [
    "Bottom-up plasticity (PG)",
    "Bottom-up plasticity (Q)",
    "Policy gradient gains",
    "Q-learning gains",
    "Rescorla-Wagner gains",
]


def _shade(color: tuple[float, float, float], factor: float = 0.6):
    return tuple(factor * c for c in color)


CONTROL_COLORS = [
    helper.COLOR_BU_PLASTICITY,
    _shade(helper.COLOR_BU_PLASTICITY),
    helper.COLOR_BACKPROP_GAIN,
    _shade(helper.COLOR_BACKPROP_GAIN),
    helper.COLOR_RESCORLA_WAGNER,
]


def simulate_condition(simulation_type: ids.SimulationType):
    # Initialize variables
    if simulation_type == NO_OFC_SIM:
        scan_type = ids.ST_FINAL
        non_stat = False
        seeds = list(range(constants.NR_SIM_MICE, 2 * constants.NR_SIM_MICE))

    elif simulation_type == OFC_SIM:
        scan_type = ids.ST_ALL
        non_stat = True
        seeds = list(range(2 * constants.NR_SIM_MICE, 3 * constants.NR_SIM_MICE))

    elif simulation_type in CONTROL_SIMS:
        scan_type = ids.ST_FINAL
        non_stat = True
        block = 3 + CONTROL_SIMS.index(simulation_type)  # Seed blocks 3 to 7
        seeds = list(
            range(block * constants.NR_SIM_MICE, (block + 1) * constants.NR_SIM_MICE)
        )

    else:
        raise NotImplementedError(simulation_type)
    scan_db_path = simulation.scan.get_db_path(
        simulation_type=simulation_type, scan_type=scan_type, non_stationary=non_stat
    )

    # Run simulations
    final_simulation(
        sim_type=simulation_type,
        scan_path=scan_db_path,
        seeds=seeds,
        save_db_path=DB_PATH,
    )


def panel_a_performance_bars(save: bool = True, verbose: bool = False) -> None:
    plot_performance_bars(
        save=save,
        db_path=DB_PATH,
        panel="a",
        plot_name="a_performance_bars",
        plot_dir=PLOT_DIR,
        colors=[COLORS[1], COLORS[0]],
        labels=["R-Opt\n+lOFC", "L-Opt\n-lOFC"],
        verbose=verbose,
    )


def panel_b_cumulative_distribution(save: bool = True) -> None:
    plot_cumulative_distribution(
        save=save,
        db_path=DB_PATH,
        panel="b",
        phase_cosmetics=False,
        plot_name="b_expertise_cumulative_distribution",
        plot_dir=PLOT_DIR,
        colors=COLORS,
        labels=["R-Opt (+lOFC)", "L-Opt (-lOFC)"],
    )


def _panel_c_config() -> FigureConfig:
    pw = 1.7 * helper.PANEL_WIDTH
    return FigureConfig(
        figure_key=keys.FIGURE_S8,
        panel="c",
        plot_name="c_expert_time",
        plot_dir=PLOT_DIR,
        panel_width=pw,
        height_ratios=(3.0, 1.0),
        width_ratios=(1.0, 2.0),
        height_scale=1.0,
        sim_types=(OFC_SIM, NO_OFC_SIM),
        db_paths=[SAVE_PATH, DB_PATH],
        colors=[COLOR_WT, COLOR_NO_OFC] + COLORS,
        labels=[
            "R-Opt mixed (intact lOFC)",
            "R-Opt mixed (silenced lOFC)",
            "R-Opt with lOFC",
            "L-Opt without lOFC",
        ],
        positions=[[1.0, 2.0], [3.0, 4.0]],
        trace_seed_loop=True,
        reversal_scatter_threshold=constants.NR_SIM_MICE / 2,
        reversal_scatter_sim_types=None,
        shade_rect_clip_on=False,
        add_fake_ofc_patch=False,
        fake_ofc_patch_target=None,
        fake_ofc_patch_color_index=None,
        rule_switch_text=(constants.NR_TRIALS - 30 * helper.PANEL_WIDTH / pw, 55),
        rule_switch_line=(0.0, -11.5, 0.0, 4.5),
        legend_axis=(0, 1),
        legend_kwargs=dict(
            loc="lower center",
            frameon=False,
            borderpad=0,
            handletextpad=0.5,
            handlelength=1,
            ncols=2,
            columnspacing=1.5,
        ),
        performance_ylabel=True,
        expertise_ylabel_kwargs=dict(rotation=0, y=0.25, labelpad=15),
        supxlabel_kwargs=dict(fontsize=helper.FONT_SIZE, x=0.55, y=0.03),
        adjust_figure_kwargs=dict(hspace=0, wspace=0),
        subplots_adjust_kwargs=dict(bottom=0.2, right=0.975),
        left_y_ticks=(
            [0.0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100.0],
            ["", "10", "", "30", "", "50", "", "70", "", "90", ""],
        ),
        bottom_xticks={
            (1, 0): ([0, 100, 200, 300, 400, 500], ["", "100", "", "", "400", ""]),
            (1, 1): (
                [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200],
                ["", "100", "", "", "400", "", "", "700", "", "", "1000", "", ""],
            ),
        },
        top_right_hide_y_ticks=True,
        y_lims_fixed=(0.0, 100.0),
        box_y_limits=(0.5, 4.5),
    )


def panel_c_expert_time(save: bool = True) -> None:
    plot_expert_time(save=save, fig_config=_panel_c_config())


def panel_d_control_algorithms(save: bool = True) -> None:
    """Mean performance traces and expert times of the control algorithms versus the
    lOFC model, all optimised for reversal learning."""
    sim_types = CONTROL_SIMS + (OFC_SIM,)
    n = len(sim_types)
    base = _panel_c_config()
    height_ratios = (3.0, 1.5)
    height_scale = 1.25  # Taller than panel c to fit one expertise row per algorithm
    # The rule-switch line spans both rows, from 100% performance down to the bottom
    # of the expertise row, in expertise-row data units (rows stacked without hspace)
    line_top = 0.5 - n * height_ratios[0] / height_ratios[1]
    fig_config = replace(
        base,
        panel="d",
        plot_name="d_control_algorithms",
        height_ratios=height_ratios,
        height_scale=height_scale,
        sim_types=sim_types,
        db_paths=[DB_PATH],
        colors=CONTROL_COLORS + [COLORS[0]],
        labels=CONTROL_LABELS + ["R-Opt with lOFC"],
        positions=[[float(p + 1) for p in range(n)]],
        plot_seed_traces=False,
        box_y_limits=(0.5, n + 0.5),
        rule_switch_line=(0.0, line_top, 0.0, n + 0.5),
        # Below all traces, which stay above chance at the rule switch
        rule_switch_text=(base.rule_switch_text[0], 27),
        # Keep panel c's absolute bottom margin despite the taller figure
        supxlabel_kwargs=dict(
            base.supxlabel_kwargs, y=base.supxlabel_kwargs["y"] / height_scale
        ),
        subplots_adjust_kwargs=dict(
            base.subplots_adjust_kwargs,
            bottom=base.subplots_adjust_kwargs["bottom"] / height_scale,
        ),
    )
    plot_expert_time(save=save, fig_config=fig_config)


def scan():
    simulation.scan.find_best_params(
        simulation_type=NO_OFC_SIM,
        task_id=TASK_ID,
        switch_task=False,
        scan_type=ids.ST_FINAL,
    )
    simulation.scan.find_best_params(
        simulation_type=OFC_SIM, task_id=TASK_ID, switch_task=True, scan_type=ids.ST_ALL
    )


def scan_control_algorithms():
    # Bottom-up plasticity based of Q learning without gain
    simulation.scan.find_best_params(
        simulation_type=ids.SIM_CONVEX_NO_GAIN_DEEP_Q,
        task_id=constants.TASK_ID,
        switch_task=True,
        scan_type=ids.ST_FINAL,
    )

    # Bottom-up plasticity based of policy gradient without gain
    simulation.scan.find_best_params(
        simulation_type=ids.SIM_CONVEX_NO_GAIN_DEEP_PG,
        task_id=constants.TASK_ID,
        switch_task=True,
        scan_type=ids.ST_FINAL,
    )

    # Rescorla-Wagner gain
    simulation.scan.find_best_params(
        simulation_type=ids.SIM_CONVEX_RW,
        task_id=constants.TASK_ID,
        switch_task=True,
        scan_type=ids.ST_FINAL,
    )

    # Backpropagated policy gradient gain
    simulation.scan.find_best_params(
        simulation_type=ids.SIM_CONVEX_PURE_PG_GAIN,
        task_id=constants.TASK_ID,
        switch_task=True,
        scan_type=ids.ST_FINAL,
    )

    # Backpropagated Q loss gain
    simulation.scan.find_best_params(
        simulation_type=ids.SIM_CONVEX_PURE_Q_GAIN,
        task_id=constants.TASK_ID,
        switch_task=True,
        scan_type=ids.ST_FINAL,
    )


def run_control_algorithms():
    for sim_type in CONTROL_SIMS:
        simulate_condition(simulation_type=sim_type)


def run():
    print("Running simulations for Figure S8")
    simulate_condition(simulation_type=OFC_SIM)
    simulate_condition(simulation_type=NO_OFC_SIM)
    run_control_algorithms()


def plot(save: bool = True):
    panel_a_performance_bars(save=save)
    panel_b_cumulative_distribution(save=save)
    panel_c_expert_time(save=save)
    panel_d_control_algorithms(save=save)
