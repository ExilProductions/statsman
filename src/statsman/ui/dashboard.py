from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from typing import Optional

from ..system_monitor import SystemMonitor
from .charts import ChartRenderer


class Dashboard:
    def __init__(self, console: Optional[Console] = None, no_color: bool = False):
        self.console = console or Console(color_system=None if no_color else "auto")
        self.monitor = SystemMonitor(history_size=120)
        self.charts = ChartRenderer(self.console)
        self.layout = Layout()
        self.sort_processes_by = "cpu"

    def _make_layout(self) -> Layout:
        """Create responsive layout based on current terminal size"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3),
        )

        layout["body"].split_column(
            Layout(name="top", ratio=2),
            Layout(name="middle", ratio=1),
            Layout(name="processes", ratio=2),
        )

        layout["top"].split_row(
            Layout(name="gauges", ratio=1),
            Layout(name="cores", ratio=1),
        )

        layout["middle"].split_row(
            Layout(name="memory", ratio=1),
            Layout(name="network", ratio=1),
        )

        return layout

    def _create_header(self) -> Panel:
        return Panel(
            Align.center(Text("StatsMan - System Monitor", style="bold blue")),
            border_style="bright_blue",
            height=3
        )

    def _create_footer(self) -> Panel:
        footer_text = (
            "[bold cyan]q[/] quit │ "
            "[bold cyan]p[/] pause │ "
            "[bold cyan]c[/] sort CPU │ "
            "[bold cyan]m[/] sort MEM"
        )
        return Panel(
            Align.center(Text.from_markup(footer_text)),
            border_style="bright_black",
            height=3
        )

    def render(self) -> Layout:
        self.layout = self._make_layout()

        self.monitor.update_history()

        self.layout["header"].update(self._create_header())
        self.layout["footer"].update(self._create_footer())

        self.layout["top"]["gauges"].update(self._create_system_gauges())
        self.layout["top"]["cores"].update(self._create_cpu_cores())

        self.layout["middle"]["memory"].update(self._create_memory_visual())
        self.layout["middle"]["network"].update(self._create_network_visual())

        self.layout["processes"].update(self._create_processes_visual())

        return self.layout

    def _create_system_gauges(self) -> Panel:
        cpu = self.monitor.get_cpu_info()
        mem = self.monitor.get_memory_info()
        disk = self.monitor.get_disk_info()
        return self.charts.create_system_gauges(cpu, mem, disk)

    def _create_cpu_cores(self) -> Panel:
        cpu = self.monitor.get_cpu_info()
        history = self.monitor.get_cpu_history()
        spark = self.charts.create_sparkline(history, height=6)
        cores = self.charts.create_cpu_core_visualization(cpu)
        return Panel(Group(Text(f"CPU Usage: {cpu.percent:.1f}%"), spark, cores),
                     title="CPU Cores", border_style="red")

    def _create_memory_visual(self) -> Panel:
        mem = self.monitor.get_memory_info()
        history = self.monitor.get_memory_history()
        spark = self.charts.create_sparkline(history, height=5)
        breakdown = self.charts.create_memory_breakdown(mem)
        return Panel(Group(Text(f"Memory: {mem.percent:.1f}%"), spark, breakdown),
                     title="Memory & Swap", border_style="green")

    def _create_network_visual(self) -> Panel:
        net = self.monitor.get_network_info()
        return self.charts.create_network_visualization(net)

    def _create_processes_visual(self) -> Panel:
        height = self.console.size.height
        limit = max(8, height // 3, 20)
        procs = self.monitor.get_process_info(limit=limit + 5)

        if self.sort_processes_by == "memory":
            procs.sort(key=lambda p: p.memory_percent, reverse=True)

        return self.charts.create_mini_process_table(procs[:limit])

    def set_process_sort(self, sort_by: str) -> None:
        if sort_by in ("cpu", "memory"):
            self.sort_processes_by = sort_by