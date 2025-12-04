from rich.console import Console, Group
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from typing import List, Dict, Any
import math


class ChartRenderer:
    def __init__(self, console: Console):
        self.console = console
    
    def create_sparkline(self, data: List[float], width: int = 80, height: int = 8) -> str:
        if not data:
            return " " * width
        
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        spark_chars = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
        recent_data = data[-width:] if len(data) > width else data
        
        sparkline = ""
        for value in recent_data:
            normalized = (value - min_val) / range_val
            char_index = min(int(normalized * len(spark_chars)), len(spark_chars) - 1)
            sparkline += spark_chars[max(0, char_index)]
        
        return sparkline
    
    def create_vertical_bars(self, data: Dict[str, float], height: int = 12, width: int = 60) -> Panel:
        if not data:
            return Panel("No data", border_style="red")
        
        max_val = max(data.values()) if data.values() else 1
        labels = list(data.keys())
        values = list(data.values())
        
        bar_widths = [int((v / max_val) * width) if max_val > 0 else 0 for v in values]
        
        lines = []
        for level in range(height, 0, -1):
            line = ""
            for bar_width in bar_widths:
                threshold = (level / height) * width
                if bar_width >= threshold:
                    line += "█"
                else:
                    line += " "
                line += "  "
            lines.append(line)
        
        label_line = ""
        for label in labels:
            label_line += f"{label[:8]:8}  "
        
        chart_text = "\n".join(lines + [label_line])
        return Panel(chart_text, border_style="blue")
    
    def create_horizontal_bars(self, data: Dict[str, float], max_width: int = 70) -> Panel:
        if not data:
            return Panel("No data", border_style="red")
        
        max_val = max(data.values()) if data.values() else 1
        
        lines = []
        for label, value in data.items():
            bar_width = int((value / max_val) * max_width) if max_val > 0 else 0
            bar = "█" * bar_width + "░" * (max_width - bar_width)
            lines.append(f"{label:6} {bar} {value:5.1f}%")
        
        return Panel("\n".join(lines), border_style="green")
    
    def create_mini_process_table(self, processes: List[Any], limit: int = 12, console_width: int = 80) -> Panel:
        if not processes:
            return Panel("No processes", border_style="red")
        
        sorted_processes = sorted(processes, key=lambda p: p.cpu_percent, reverse=True)
        
        max_name_width = max(10, min(20, (console_width - 35) // 2))
        bar_width = max(5, min(10, (console_width - 25) // 4))
        
        header = f"{'PID':<7} {'PROCESS':<20} {'CPU':<12} {'MEM':<12}"
        separator = "=" * min(console_width - 4, 75)
        lines = [header, separator]
        
        for proc in sorted_processes[:limit]:
            cpu_bar = self._create_mini_bar(proc.cpu_percent, bar_width)
            mem_bar = self._create_mini_bar(proc.memory_percent, bar_width)
            
            name = (proc.name[:18] + "..") if len(proc.name) > 20 else proc.name.ljust(20)
            lines.append(f"{proc.pid:<7} {name} {cpu_bar} {mem_bar}")
        
        return Panel("\n".join(lines), title="Top Processes", border_style="magenta")
    
    def _create_mini_bar(self, percentage: float, width: int = 10) -> str:
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar
    
    def create_system_gauges(self, cpu_info: Any, memory_info: Any, disk_info: Any, console_width: int = 80) -> Panel:
        gauges = []
        gauge_width = max(15, min(30, console_width // 4))
        
        cpu_gauge = self._create_gauge(cpu_info.percent, "CPU", gauge_width)
        gauges.append(cpu_gauge)
        
        mem_gauge = self._create_gauge(memory_info.percent, "MEM", gauge_width)
        gauges.append(mem_gauge)
        
        disk_gauge = self._create_gauge(disk_info.percent, "DSK", gauge_width)
        gauges.append(disk_gauge)
        
        return Panel(Group(*gauges), border_style="cyan")
    
    def _create_gauge(self, percentage: float, label: str, width: int = 30) -> Text:
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return Text.from_markup(f"[bold]{label}:[/bold] {bar} {percentage:5.1f}%")
    
    def create_network_visualization(self, network_info: Any, console_width: int = 80) -> Panel:
        sent_mb = network_info.bytes_sent / (1024 * 1024)
        recv_mb = network_info.bytes_recv / (1024 * 1024)
        
        network_data = {
            "UPLOAD": min(sent_mb * 10, 100),
            "DOWNLOAD": min(recv_mb * 10, 100),
        }
        
        bar_width = max(15, min(70, console_width // 2))
        return self.create_horizontal_bars(network_data, max_width=bar_width)
    
    def create_cpu_core_visualization(self, cpu_info: Any, console_width: int = 80) -> Panel:
        if not cpu_info.percent_per_core:
            return Panel("No core data", border_style="red")
        
        core_data = {}
        for i, core_percent in enumerate(cpu_info.percent_per_core):
            core_data[f"C{i:02d}"] = core_percent
        
        bar_width = max(20, min(40, console_width // 8))
        return self.create_vertical_bars(core_data, height=8, width=bar_width)
    
    def create_memory_breakdown(self, memory_info: Any, console_width: int = 80) -> Panel:
        used_gb = memory_info.used / (1024**3)
        total_gb = memory_info.total / (1024**3)
        
        memory_data = {
            "USED": (used_gb / total_gb) * 100,
            "FREE": ((total_gb - used_gb) / total_gb) * 100,
        }
        
        bar_width = max(15, min(70, console_width // 2))
        return self.create_horizontal_bars(memory_data, max_width=bar_width)
    
    def format_bytes(self, bytes_value: int) -> str:
        bytes_float = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_float < 1024.0:
                return f"{bytes_float:.1f} {unit}"
            bytes_float /= 1024.0
        return f"{bytes_float:.1f} PB"