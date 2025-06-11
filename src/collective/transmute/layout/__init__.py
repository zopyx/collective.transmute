"""
Layout and UI components for collective.transmute.

This module provides rich terminal UI components for displaying progress,
reports, and status information during the data transformation process.
It uses the Rich library to create beautiful, interactive terminal interfaces.
"""

from collective.transmute import _types as t
from collective.transmute.utils import sort_data
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.table import Table


class Header:
    """Display header for the application.
    
    Creates a header panel with the application title and current operation.
    """

    def __init__(self, title: str):
        """Initialize the header with a title.
        
        Args:
            title: Title to display in the header
        """
        self.title = title

    def __rich__(self) -> Panel:
        """Render the header as a Rich panel.
        
        Returns:
            Rich panel containing the header information
        """
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row("[b]collective.transmute[/b]")
        grid.add_row(f"[b]{self.title}[/b]")
        return Panel(grid, style="white on blue")


class TransmuteReport:
    """Report metadata display component.
    
    Displays statistics and metadata information in a formatted panel.
    """

    def __init__(self, data: dict[str, int], title: str):
        """Initialize the report with data and title.
        
        Args:
            data: Dictionary of data to display
            title: Title for the report panel
        """
        self.title = title
        self.data = data

    def __rich__(self) -> Panel:
        """Render the report as a Rich panel.
        
        Returns:
            Rich panel containing the report data
        """
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=2)
        grid.add_column(justify="right", ratio=1)
        for name, total in sort_data(self.data):
            grid.add_row(name, f"{total}")
        return Panel(grid, title=self.title, border_style="green")


def progress_panel(progress: t.PipelineProgress | t.ReportProgress) -> Panel:
    """Create a progress panel for display.
    
    Creates a panel containing progress bars for tracking operation progress.
    
    Args:
        progress: Progress tracking object
        
    Returns:
        Rich panel containing progress information
    """
    progress_table = Table.grid(expand=True)
    progress_table.add_row(progress.processed)
    if isinstance(progress, t.PipelineProgress):
        progress_table.add_row(progress.dropped)
    return Panel(
        progress_table,
        title="[b]Progress",
        border_style="green",
    )


def create_consoles() -> t.ConsoleArea:
    """Create console area with two console panels.
    
    Returns:
        ConsoleArea object with main and side console panels
    """
    main_console = t.ConsolePanel()
    side_console = t.ConsolePanel()
    return t.ConsoleArea(main_console, side_console)


class ApplicationLayout:
    """Base application layout class.
    
    Provides the foundation for different application layouts with
    common functionality for progress tracking and layout management.
    """
    title: str
    layout: Layout
    consoles: t.ConsoleArea
    progress: t.ReportProgress | t.PipelineProgress

    def __init__(self, title: str):
        """Initialize the application layout.
        
        Args:
            title: Title for the application
        """
        self.consoles = create_consoles()
        self.layout = self._create_layout(title)
        self.title = title

    def _create_layout(self, title: str) -> Layout:
        """Create the base layout structure.
        
        Args:
            title: Title for the layout
            
        Returns:
            Rich layout object
        """
        return Layout(name="root")

    def update_layout(self, state: t.PipelineState | t.ReportState):
        """Update the layout with current state.
        
        Args:
            state: Current state object to display
        """
        pass

    def initialize_progress(self, total: int):
        """Initialize progress tracking.
        
        Args:
            total: Total number of items to process
        """
        pass


class TransmuteLayout(ApplicationLayout):
    """Layout for the main transmute operation.
    
    Provides a comprehensive layout for the data transformation process
    with progress tracking, logging, and statistics display.
    """
    def _create_layout(self, title: str) -> Layout:
        """Create the transmute-specific layout.
        
        Args:
            title: Title for the layout
            
        Returns:
            Rich layout object configured for transmute operations
        """
        consoles = self.consoles
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", ratio=1),
            Layout(name="main", ratio=5),
            Layout(name="footer", ratio=1),
        )
        layout["main"].split_row(
            Layout(name="body", ratio=5, minimum_size=60),
            Layout(name="side", ratio=2),
        )
        layout["header"].update(Header(title=title))
        layout["body"].update(
            Panel(consoles.main, title="[b]Log", border_style="green"),
        )
        layout["side"].update(
            Panel("", title="[b]Report", border_style="green"),
        )
        layout["footer"].update(
            Panel("", title="[b]Progress", border_style="green"),
        )
        return layout

    def update_layout(self, state: t.PipelineState):
        """Update the layout with current pipeline state.
        
        Args:
            state: Current pipeline state to display
        """
        layout = self.layout
        layout["footer"].update(progress_panel(state.progress))
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_row(TransmuteReport(state.exported, "Transmuted"))
        grid.add_row(TransmuteReport(state.dropped, "Dropped"))
        layout["side"].update(
            Panel(
                grid,
                title="[b]Report",
                border_style="green",
            ),
        )

    def initialize_progress(self, total: int):
        """Initialize progress tracking for transmute operations.
        
        Args:
            total: Total number of items to process
        """
        processed = Progress(
            "{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%[/progress.percentage] "
                "({task.completed}/{task.total})"
            ),
            expand=True,
        )
        dropped = Progress(
            "{task.description}",
            SpinnerColumn(),
            TextColumn("{task.completed}"),
        )
        processed_id = processed.add_task("[green]Processed", total=total)
        dropped_id = dropped.add_task("[red]Dropped")
        self.progress = t.PipelineProgress(processed, processed_id, dropped, dropped_id)


class ReportLayout(ApplicationLayout):
    """Layout for report generation operations.
    
    Provides a layout optimized for displaying report information
    with statistics and progress tracking.
    """
    def _create_layout(self, title: str) -> Layout:
        """Create the report-specific layout.
        
        Args:
            title: Title for the layout
            
        Returns:
            Rich layout object configured for report operations
        """
        consoles = self.consoles
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", ratio=1),
            Layout(name="main", ratio=4),
            Layout(name="body", ratio=2),
            Layout(name="footer", ratio=1),
        )
        layout["header"].update(Header(title=title))
        layout["body"].update(
            Panel(consoles.main, title="[b]Log", border_style="green"),
        )
        layout["main"].update(
            Panel("", title="[b]Report", border_style="green"),
        )
        layout["footer"].update(
            Panel("", title="[b]Progress", border_style="green"),
        )
        return layout

    def update_layout(self, state: t.ReportState):
        """Update the layout with current report state.
        
        Args:
            state: Current report state to display
        """
        layout = self.layout
        layout["footer"].update(progress_panel(state.progress))
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="left", ratio=1)
        row = []
        for name in ("Types", "States", "Creators"):
            data = getattr(state, name.lower())
            row.append(TransmuteReport(data, name))
        grid.add_row(*row)
        layout["main"].update(
            Panel(
                grid,
                title="[b]Report",
                border_style="green",
            ),
        )

    def initialize_progress(self, total: int):
        """Initialize progress tracking for report operations.
        
        Args:
            total: Total number of items to process
        """
        processed = Progress(
            "{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%[/progress.percentage] "
                "({task.completed}/{task.total})"
            ),
            expand=True,
        )
        processed_id = processed.add_task("[green]Processed", total=total)
        self.progress = t.ReportProgress(processed, processed_id)


def live(app_layout: ApplicationLayout, redirect_stderr: bool = True) -> Live:
    """Create a live display for the application layout.
    
    Creates a live updating display that shows the current state of the
    application layout in real-time.
    
    Args:
        app_layout: Application layout to display
        redirect_stderr: Whether to redirect stderr to the display
        
    Returns:
        Rich Live display object
    """
    return Live(
        app_layout.layout,
        refresh_per_second=4,
        redirect_stderr=redirect_stderr,
    )
