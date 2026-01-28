"""
Luna Autonomous Digital Twin - Main Entry Point

A fully autonomous AI system that learns your decision patterns and
makes decisions across Business, Finance, Health, and Daily Life.
"""

# Configure logging FIRST to ensure clean console output
import utils.logging_config  # noqa: F401, E402

import os
import sys
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich import print as rprint
from rich.prompt import Prompt

# Initialize Rich Console
console = Console()
load_dotenv()

# Import Luna modules
try:
    from config import config
    from core.decision_engine import get_decision_engine, DecisionEngine
    from core.memory_system import get_memory_system
    from models import MemoryType, MemoryTier
    from core.review_system import ReviewSystem
    from core.scheduler import ProactiveScheduler
    # Multi-agent system imports
    from core.agents.registry import get_agent_registry
    from core.agents.teams import create_coding_team, create_marketing_team
    from core.agents.patterns import run_brainstorm_session
except ImportError as e:
    console.print(f"[bold red]Error importing Luna modules: {e}[/bold red]")
    console.print("[yellow]Please ensure all dependencies are installed.[/yellow]")
    sys.exit(1)


class LunaCLI:
    """Command-line interface for Luna"""

    def __init__(self):
        """Initialize Luna CLI"""
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            console.print(f"[bold red]Configuration Error: {e}[/bold red]")
            console.print("[yellow]Please check your .env file and ensure GEMINI_API_KEY is set.[/yellow]")
            sys.exit(1)

        # Initialize core components
        try:
            with console.status("[bold green]Initializing Luna Core Systems...[/bold green]"):
                self.decision_engine = get_decision_engine()
                self.memory_system = get_memory_system()
                self.review_system = ReviewSystem()
                
                # Initialize scheduler
                self.scheduler = ProactiveScheduler(self.decision_engine.tool_registry)
                self.scheduler.start()
        except Exception as e:
            console.print(f"[bold red]Initialization Failed: {e}[/bold red]")
            sys.exit(1)

        # Session stats
        self.session_start = time.time()
        self.decisions_made = 0
        
        # Initialize multi-agent teams (lazy)
        self.agent_registry = None
        self.teams_initialized = False

    def print_header(self):
        """Print Luna header"""
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(
            Panel(
                Align.center(
                    Text("LUNA AUTONOMOUS DIGITAL TWIN", style="bold cyan", justify="center")
                ),
                subtitle=f"Memory: {config.memory.path} | Domains: {', '.join(DecisionEngine.DOMAINS)}",
                style="cyan"
            )
        )
        console.print(grid)
        console.print()

    def print_help(self):
        """Print help information"""
        table = Table(title="Available Commands", border_style="yellow")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Example", style="dim")

        table.add_row("learn: [fact]", "Teach Luna a fact", "learn: I prefer Python")
        table.add_row("finance: [q]", "Finance decisions", "finance: Should I buy BTC?")
        table.add_row("business: [q]", "Business decisions", "business: Prioritize tasks")
        table.add_row("health: [q]", "Health decisions", "health: Sleep analysis")
        table.add_row("life: [q]", "Life decisions", "life: Orgnaize my schedule")
        table.add_row("remember/forget", "Manage memory", "forget: pattern")
        table.add_row("status", "Show system state", "status")
        table.add_row("review", "Review decisions", "review")
        table.add_row("analyze: [q]", "Deep Gemini analysis", "analyze: Market trends")
        table.add_row("monitor:btc", "Launch BTC Monitor", "monitor:btc")
        table.add_row("", "", "")
        table.add_row("[bold magenta]--- MULTI-AGENT TEAMS ---[/bold magenta]", "", "")
        table.add_row("team:coding [task]", "Delegate to coding team", "team:coding create hello world")
        table.add_row("team:marketing [task]", "Delegate to marketing team", "team:marketing analyze market")
        table.add_row("brainstorm: [topic]", "Joint-chat brainstorm", "brainstorm: improve UX")
        table.add_row("teams", "Show team status", "teams")
        table.add_row("exit / quit", "Shutdown Luna", "exit")

        console.print(table)
        console.print()

    def handle_learn(self, fact: str):
        """Handle learn command - add memory"""
        if not fact:
            console.print("[bold red]Error: Please provide a fact to learn[/bold red]")
            return

        self.memory_system.add_memory(
            text=fact,
            category="user_rule",
            memory_type=MemoryType.USER_PREFERENCE,
            tier=MemoryTier.LONG_TERM
        )
        console.print(Panel(f"[bold green]LEARNED:[/bold green] {fact}", title="Memory Update"))

    def handle_domain_query(self, domain: str, query: str):
        """Handle domain-specific query"""
        if not query:
            console.print(f"[bold red]Error: Please provide a question for {domain} domain[/bold red]")
            return

        with console.status(f"[bold magenta]Luna is processing {domain} decision...[/bold magenta]"):
            result = self.decision_engine.make_decision(query, domain_hint=domain)

        # Print formatted result
        if result.analysis and "API Quota" in result.analysis:
            console.print(f"[bold yellow][!] SYSTEM NOTICE: {result.analysis}[/bold yellow]")

        # Create a nice layout for the result
        result_panel = Panel(
            Markdown(result.format_output()),
            title=f"Decision: {domain.upper()}",
            border_style="cyan"
        )
        console.print(result_panel)

        # Update stats
        self.decisions_made += 1

    def handle_general_query(self, query: str):
        """Handle general query (auto-classify domain)"""
        with console.status("[bold magenta]Luna is processing...[/bold magenta]"):
            result = self.decision_engine.make_decision(query)

        # Print formatted result
        console.print(Panel(
            Markdown(result.format_output()),
            title="Decision Result",
            border_style="cyan"
        ))

        # Update stats
        self.decisions_made += 1

    def handle_status(self):
        """Handle status command"""
        memory_stats = self.memory_system.get_stats()
        
        table = Table(title="Luna System Status", border_style="cyan")
        table.add_column("Metric", style="white")
        table.add_column("Value", style="green")
        
        table.add_row("Session Duration", f"{int(time.time() - self.session_start)}s")
        table.add_row("Decisions Made", str(self.decisions_made))
        table.add_row("Short-term Memories", str(memory_stats.get('short_term_count', 0)))
        table.add_row("Long-term Memories", str(memory_stats.get('total_memories', 0)))
        
        console.print(table)
        
        # Breakdown
        if memory_stats.get('collections'):
            subtable = Table(title="Memory Collections", show_header=False, box=None)
            for collection, count in memory_stats.get('collections', {}).items():
                if count > 0:
                    subtable.add_row(collection, str(count))
            console.print(subtable)
        console.print()

    def handle_review(self):
        """Interactive review session"""
        pending = self.review_system.get_pending_reviews()
        if not pending:
            console.print("[bold green]No pending reviews! All caught up.[/bold green]")
            return
            
        console.print(f"[bold cyan]Found {len(pending)} decisions to review:[/bold cyan]")
        
        for i, decision in enumerate(pending):
            console.rule(f"Decision {i+1}/{len(pending)}")
            console.print(f"[bold]Input:[/bold] {decision['metadata'].get('user_input', 'Unknown')}")
            console.print(f"[bold green]Luna:[/bold green] {decision['document'][:200]}...")
            
            try:
                rating = Prompt.ask("Rate this decision (1-5) or 'skip'", default="skip")
                if rating.lower() == 'skip':
                    continue
                    
                if rating.isdigit() and 1 <= int(rating) <= 5:
                    comments = Prompt.ask("Comments (optional)")
                    self.review_system.submit_feedback(decision['decision_id'], int(rating), comments)
                else:
                    console.print("[red]Invalid rating. Skipping.[/red]")
            except KeyboardInterrupt:
                break
        console.print("[bold cyan]Review session complete.[/bold cyan]")

    def handle_deep_analysis(self, query: str):
        """Handle analysis via Gemini"""
        console.rule("[bold magenta]LUNA DEEP ANALYSIS[/bold magenta]")
        
        with console.status("[bold magenta]Thinking...[/bold magenta]"):
            result = self.decision_engine.perform_deep_analysis(query)
        
        if result.get("success"):
            console.print(Markdown(result["analysis"]))
            self.decisions_made += 1
        else:
            console.print(f"[bold red]Analysis failed: {result.get('error')}[/bold red]")
        console.rule()

    def _init_teams(self):
        """Lazily initialize multi-agent teams"""
        if self.teams_initialized:
            return
        
        with console.status("[bold magenta]Initializing Multi-Agent Teams...[/bold magenta]"):
            self.agent_registry = get_agent_registry()
            
            # Create executive (Luna)
            self.agent_registry.create_executive("Luna Executive")
            
            # Create teams with configured providers
            coding_provider = config.teams.coding_provider
            marketing_provider = config.teams.marketing_provider
            
            # Fallback to gemini if ZAI key not available
            if coding_provider == "zai" and not config.zai.api_key:
                console.print("[yellow]ZAI_API_KEY not set, using Gemini for coding team[/yellow]")
                coding_provider = "gemini"
            
            create_coding_team(provider=coding_provider)
            create_marketing_team(provider=marketing_provider)
            
        self.teams_initialized = True
        console.print("[green]Multi-agent teams ready![/green]")

    def handle_team_task(self, team_name: str, task: str):
        """Handle team delegation command"""
        if not task:
            console.print(f"[bold red]Error: Please provide a task for {team_name} team[/bold red]")
            return
        
        self._init_teams()
        
        team_info = self.agent_registry.get_team(team_name)
        if not team_info:
            console.print(f"[bold red]Error: Team '{team_name}' not found[/bold red]")
            return
        
        manager = team_info["manager"]
        
        with console.status(f"[bold magenta]{manager.name} is working on your task...[/bold magenta]"):
            result = manager.execute(task)
        
        # Display results
        console.rule(f"[bold cyan]{team_name.upper()} TEAM RESULT[/bold cyan]")
        
        if result.get("success"):
            # Show each phase
            for phase in result.get("phases", []):
                phase_name = phase.get("phase", "unknown").upper()
                worker = phase.get("worker", "Unknown")
                output = phase.get("result", {}).get("output", "No output")
                
                console.print(Panel(
                    Markdown(output[:2000] + "..." if len(output) > 2000 else output),
                    title=f"{phase_name} - {worker}",
                    border_style="green"
                ))
        else:
            console.print(f"[bold red]Task failed: {result.get('error')}[/bold red]")
        
        console.rule()
        self.decisions_made += 1

    def handle_brainstorm(self, topic: str):
        """Handle brainstorming session"""
        if not topic:
            console.print("[bold red]Error: Please provide a topic to brainstorm[/bold red]")
            return
        
        self._init_teams()
        
        console.print(f"[bold magenta]Starting brainstorm session on: {topic}[/bold magenta]")
        console.print("[dim]This may take a few minutes as multiple agents discuss...[/dim]")
        console.print()
        
        with console.status("[bold magenta]Agents are brainstorming...[/bold magenta]"):
            result = run_brainstorm_session(
                topic=topic,
                rounds=config.teams.brainstorm_rounds,
                provider="gemini"
            )
        
        # Display discussion
        console.rule(f"[bold cyan]BRAINSTORM: {topic}[/bold cyan]")
        
        for entry in result.get("discussion", []):
            speaker = entry.get("speaker", "Unknown")
            content = entry.get("content", "")
            entry_type = entry.get("type", "")
            
            if entry_type == "synthesis":
                console.print(Panel(
                    Markdown(content),
                    title="FINAL SYNTHESIS",
                    border_style="green"
                ))
            else:
                console.print(f"[bold cyan]{speaker}:[/bold cyan]")
                console.print(Markdown(content[:1000]))
                console.print()
        
        console.rule()
        self.decisions_made += 1

    def handle_team_status(self):
        """Display status of all teams"""
        self._init_teams()
        
        status = self.agent_registry.get_team_status()
        
        table = Table(title="Multi-Agent Teams", border_style="magenta")
        table.add_column("Team", style="cyan")
        table.add_column("Manager", style="white")
        table.add_column("Workers", style="green")
        table.add_column("Provider", style="yellow")
        
        for team_name, info in status.items():
            workers = ", ".join([w["name"] for w in info["workers"]])
            table.add_row(
                team_name.upper(),
                info["manager"],
                workers,
                info["provider"]
            )
        
        console.print(table)

    def run(self):
        """Run the Luna CLI"""
        self.print_header()
        console.print("[yellow]Type 'help' for available commands[/yellow]")
        console.print()

        from rich.align import Align
        from rich.text import Text

        while True:
            try:
                # Check for alerts
                alerts = self.scheduler.get_alerts()
                if alerts:
                    console.print()
                    console.print("[bold red] [!] NEW ALERTS:[/bold red]")
                    for alert in alerts:
                        console.print(f"[red]  * [{alert['source']}] {alert['message']}[/red]")
                    console.print()
                
                user_input = Prompt.ask("[bold white]Input[/bold white]")

                if not user_input:
                    continue

                # Exit commands
                if user_input.lower() in ['exit', 'quit']:
                    console.print(f"[cyan]Session complete. Decisions made: {self.decisions_made}[/cyan]")
                    self.scheduler.stop()
                    break

                # Help command
                if user_input.lower() == 'help':
                    self.print_help()
                    continue

                # Status command
                if user_input.lower() == 'status':
                    self.handle_status()
                    continue

                if user_input.lower() == 'review':
                    self.handle_review()
                    continue
                
                if user_input.lower() == 'monitor:btc':
                     import subprocess
                     console.print("[green]Launching BTC Position Monitor...[/green]")
                     subprocess.Popen([sys.executable, "btc_position_monitor.py"])
                     continue

                if user_input.lower().startswith("analyze:"):
                    query = user_input[8:].strip()
                    self.handle_deep_analysis(query)
                    continue

                # Learn command (backwards compatible)
                if user_input.lower().startswith("learn:"):
                    fact = user_input[6:].strip()
                    self.handle_learn(fact)
                    continue

                # Domain-specific commands
                if user_input.lower().startswith("finance:"):
                    query = user_input[8:].strip()
                    self.handle_domain_query("finance", query)
                    continue

                if user_input.lower().startswith("business:"):
                    query = user_input[9:].strip()
                    self.handle_domain_query("business", query)
                    continue

                if user_input.lower().startswith("health:"):
                    query = user_input[7:].strip()
                    self.handle_domain_query("health", query)
                    continue

                if user_input.lower().startswith("life:"):
                    query = user_input[5:].strip()
                    self.handle_domain_query("daily_life", query)
                    continue

                # Multi-agent team commands
                if user_input.lower().startswith("team:coding"):
                    task = user_input[11:].strip()
                    self.handle_team_task("coding", task)
                    continue

                if user_input.lower().startswith("team:marketing"):
                    task = user_input[14:].strip()
                    self.handle_team_task("marketing", task)
                    continue

                if user_input.lower().startswith("brainstorm:"):
                    topic = user_input[11:].strip()
                    self.handle_brainstorm(topic)
                    continue

                if user_input.lower() == 'teams':
                    self.handle_team_status()
                    continue

                # General query (auto-classify domain)
                self.handle_general_query(user_input)

            except KeyboardInterrupt:
                console.print(f"\n\n[cyan]Session interrupted. Decisions made: {self.decisions_made}[/cyan]")
                break
            except Exception as e:
                console.print(f"[bold red]Error: {e}[/bold red]")
                continue


def main():
    """Main entry point"""
    cli = LunaCLI()
    cli.run()


if __name__ == "__main__":
    main()
