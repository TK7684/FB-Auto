"""
CSV Fixer Unified Application

A comprehensive GUI application for fixing CSV files for BigQuery compatibility.
Combines all CSV fixing functionality into one unified interface.
"""

import os
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import List, Dict, Any, Optional
import threading
from datetime import datetime

# Add the csv_fixer_core module to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from csv_fixer_core import (
    Config,
    HistoryManager,
    ProcessingRecord,
    process_csv_file,
    process_csv_pandas,
    process_creator_order_csv,
    fix_header_only,
    detect_file_encoding,
    get_file_info,
    validate_csv_structure,
    get_output_filename,
    ensure_directory_exists,
    load_config,
    save_config,
    get_config_path,
    init_logging,
    get_logger
)

from csv_fixer_core.constants import (
    APP_TITLE,
    CSV_FILTERS,
    FIX_OPTIONS,
    THEME_COLORS,
    FONTS
)


class ProgressDialog:
    """Progress dialog for long-running operations."""

    def __init__(self, parent: tk.Tk, title: str = "Processing..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Apply background color
        try:
            from csv_fixer_core.constants import THEME_COLORS
            # Use light theme by default if config not accessible, or basic white
            bg_color = THEME_COLORS["light"]["bg"]
            self.dialog.configure(bg=bg_color)
        except:
            pass

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"400x200+{x}+{y}")

        # Create main frame
        self.main_frame = ttk.Frame(self.dialog, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create widgets
        ttk.Label(self.main_frame, text="Processing files...", font=FONTS["header"]).pack(pady=(0, 20))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            variable=self.progress_var,
            maximum=100,
            length=350,
            mode='determinate'
        )
        self.progress_bar.pack(pady=(0, 10), fill=tk.X)

        self.status_label = ttk.Label(self.main_frame, text="Initializing...", font=FONTS["body"])
        self.status_label.pack(pady=(0, 20))

        self.cancel_button = ttk.Button(
            self.main_frame,
            text="Cancel",
            command=self.cancel
        )
        self.cancel_button.pack()

        self.cancelled = False

    def update_progress(self, value: int, status: str = ""):
        """Update progress bar and status."""
        self.progress_var.set(value)
        if status:
            self.status_label.config(text=status)
        self.dialog.update()

    def cancel(self):
        """Cancel the operation."""
        self.cancelled = True
        self.status_label.config(text="Cancelling...")

    def close(self):
        """Close the dialog."""
        self.dialog.destroy()


class HistoryWindow:
    """Window for viewing processing history."""

    def __init__(self, parent: tk.Tk, history_manager: HistoryManager):
        self.history_manager = history_manager
        self.window = tk.Toplevel(parent)
        self.window.title("Processing History")
        self.window.geometry("900x600")

        self.create_widgets()
        self.load_history()

    def create_widgets(self):
        """Create history window widgets."""
        # Main container with padding
        main_container = ttk.Frame(self.window, padding=20)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar = ttk.Frame(main_container, style="Card.TFrame", padding=10)
        toolbar.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(
            toolbar,
            text="Refresh",
            command=self.load_history
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            toolbar,
            text="Export to CSV",
            command=self.export_history
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            toolbar,
            text="Clear History",
            command=self.clear_history
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(toolbar, text="Search:", font=FONTS["body_bold"]).pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.search_var, width=30, font=FONTS["body"]).pack(side=tk.LEFT, padx=5)

        # Treeview frame
        tree_frame = ttk.Frame(main_container, style="Card.TFrame", padding=2)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for history
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("timestamp", "input", "output", "rows", "fixes", "status"),
            show="headings",
            style="Treeview"
        )
        
        # Configure scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Define columns
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("input", text="Input File")
        self.tree.heading("output", text="Output File")
        self.tree.heading("rows", text="Rows")
        self.tree.heading("fixes", text="Fixes Applied")
        self.tree.heading("status", text="Status")

        # Configure column widths
        self.tree.column("timestamp", width=150)
        self.tree.column("input", width=250)
        self.tree.column("output", width=250)
        self.tree.column("rows", width=80)
        self.tree.column("fixes", width=200)
        self.tree.column("status", width=80)

        # Pack widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind events
        self.tree.bind('<Double-1>', self.show_details)
        
        # Bind search
        # Note: ttk.Entry doesn't support binding directly to variable updates easily without trace
        self.search_var.trace_add("write", lambda *args: self.on_search())

    def load_history(self):
        """Load history records."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get records
        records = self.history_manager.get_records(limit=200)

        # Add records to tree
        for record in records:
            status = "Success" if record.success else "Error"
            fixes = ", ".join(record.fixes_applied[:3])
            if len(record.fixes_applied) > 3:
                fixes += f"... (+{len(record.fixes_applied) - 3})"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    record.timestamp[:19] if record.timestamp else "",
                    os.path.basename(record.input_file),
                    os.path.basename(record.output_file),
                    record.rows_processed,
                    fixes,
                    status
                ),
                tags=(status.lower(),)
            )

        # Configure tags
        self.tree.tag_configure("success", foreground=THEME_COLORS["light"]["success"])
        self.tree.tag_configure("error", foreground=THEME_COLORS["light"]["error"])

    def on_search(self, event=None):
        """Handle search."""
        search_term = self.search_var.get().lower()
        if not search_term:
            # If search is cleared, reload full history only if we were previously filtered
            # But since this is a trace callback, we can just reload
            self.load_history()
            return

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Search records
        records = self.history_manager.search_records(search_term)

        # Add matching records
        for record in records:
            status = "Success" if record.success else "Error"
            fixes = ", ".join(record.fixes_applied[:3])
            if len(record.fixes_applied) > 3:
                fixes += f"... (+{len(record.fixes_applied) - 3})"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    record.timestamp[:19] if record.timestamp else "",
                    os.path.basename(record.input_file),
                    os.path.basename(record.output_file),
                    record.rows_processed,
                    fixes,
                    status
                ),
                tags=(status.lower(),)
            )

    def show_details(self, event):
        """Show details for selected record."""
        selection = self.tree.selection()
        if not selection:
            return

        # Get the record ID from the tree (we'd need to store it)
        # For now, show a simple message
        messagebox.showinfo(
            "Details",
            "Double-click functionality to be implemented with record ID tracking"
        )

    def export_history(self):
        """Export history to CSV."""
        filename = filedialog.asksaveasfilename(
            title="Export History",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if filename:
            try:
                self.history_manager.export_to_csv(filename)
                messagebox.showinfo("Success", f"History exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export history: {e}")

    def clear_history(self):
        """Clear processing history."""
        if messagebox.askyesno(
            "Clear History",
            "Are you sure you want to clear the processing history?\n\n"
            "This action cannot be undone."
        ):
            try:
                count = self.history_manager.clear_history()
                messagebox.showinfo("Success", f"Cleared {count} records from history")
                self.load_history()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {e}")


class SettingsWindow:
    """Window for application settings."""

    def __init__(self, parent: tk.Tk, config: Config):
        self.config = config
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("500x500")
        self.window.transient(parent)
        self.window.grab_set()

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        """Create settings widgets."""
        # Create notebook for categorized settings
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # General tab
        general_frame = ttk.Frame(notebook, padding=20)
        notebook.add(general_frame, text="General")

        # Output directory
        ttk.Label(general_frame, text="Default Output Directory:", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        output_frame = ttk.Frame(general_frame)
        output_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.output_dir_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_dir_var, font=FONTS["body"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(output_frame, text="Browse", command=self.browse_output_dir).pack(side=tk.LEFT)

        # Checkboxes
        options_frame = ttk.Frame(general_frame, style="Card.TFrame", padding=15)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.auto_open_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Auto-open output folder after processing",
            variable=self.auto_open_var,
            style="TCheckbutton"
        ).pack(anchor=tk.W, pady=2)

        self.create_backups_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Create backup files before processing",
            variable=self.create_backups_var,
            style="TCheckbutton"
        ).pack(anchor=tk.W, pady=2)

        self.save_logs_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Save processing logs",
            variable=self.save_logs_var,
            style="TCheckbutton"
        ).pack(anchor=tk.W, pady=2)

        self.use_fast_mode_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Use Fast Mode (Pandas) - Recommended for large files",
            variable=self.use_fast_mode_var,
            style="TCheckbutton"
        ).pack(anchor=tk.W, pady=2)

        # Processing tab
        processing_frame = ttk.Frame(notebook, padding=20)
        notebook.add(processing_frame, text="Processing")

        ttk.Label(processing_frame, text="Default Fix Options:", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        fix_frame = ttk.Frame(processing_frame, style="Card.TFrame", padding=15)
        fix_frame.pack(fill=tk.X)

        self.fix_options_vars = {}
        for i, (key, option) in enumerate(FIX_OPTIONS.items(), start=1):
            var = tk.BooleanVar()
            self.fix_options_vars[key] = var
            ttk.Checkbutton(
                fix_frame,
                text=option["name"],
                variable=var,
                style="TCheckbutton"
            ).pack(anchor=tk.W, pady=2)

        # UI tab
        ui_frame = ttk.Frame(notebook, padding=20)
        notebook.add(ui_frame, text="Appearance")
        
        ui_card = ttk.Frame(ui_frame, style="Card.TFrame", padding=15)
        ui_card.pack(fill=tk.X)

        ttk.Label(ui_card, text="Theme:", font=FONTS["body_bold"]).grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(ui_card, textvariable=self.theme_var, values=["light", "dark"], state="readonly", font=FONTS["body"])
        theme_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=10)

        ttk.Label(ui_card, text="Window Size:", font=FONTS["body_bold"]).grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        size_frame = ttk.Frame(ui_card)
        size_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)

        ttk.Label(size_frame, text="Width:", font=FONTS["body"]).pack(side=tk.LEFT)
        self.window_width_var = tk.IntVar()
        tk.Spinbox(size_frame, from_=800, to=1920, textvariable=self.window_width_var, width=8, font=FONTS["body"]).pack(side=tk.LEFT, padx=5)

        ttk.Label(size_frame, text="Height:", font=FONTS["body"]).pack(side=tk.LEFT, padx=(10, 0))
        self.window_height_var = tk.IntVar()
        tk.Spinbox(size_frame, from_=600, to=1080, textvariable=self.window_height_var, width=8, font=FONTS["body"]).pack(side=tk.LEFT, padx=5)

        # History tab
        history_frame = ttk.Frame(notebook, padding=20)
        notebook.add(history_frame, text="History")
        
        hist_card = ttk.Frame(history_frame, style="Card.TFrame", padding=15)
        hist_card.pack(fill=tk.X)

        self.keep_history_var = tk.BooleanVar()
        ttk.Checkbutton(
            hist_card,
            text="Keep processing history",
            variable=self.keep_history_var,
            style="TCheckbutton"
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)

        ttk.Label(hist_card, text="Maximum history records:", font=FONTS["body"]).grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        self.max_history_var = tk.IntVar()
        tk.Spinbox(hist_card, from_=100, to=10000, increment=100, textvariable=self.max_history_var, font=FONTS["body"]).grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)

        # Buttons
        button_frame = ttk.Frame(self.window, padding=20)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_defaults).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Save", command=self.save_settings, style="Primary.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT)

    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)

    def load_settings(self):
        """Load settings from config."""
        self.output_dir_var.set(self.config.output_directory)
        self.auto_open_var.set(self.config.auto_open_output)
        self.create_backups_var.set(self.config.create_backups)
        self.save_logs_var.set(self.config.save_logs)
        self.use_fast_mode_var.set(getattr(self.config, 'use_fast_mode', True))
        self.theme_var.set(self.config.theme)
        self.window_width_var.set(self.config.window_width)
        self.window_height_var.set(self.config.window_height)
        self.keep_history_var.set(self.config.keep_history)
        self.max_history_var.set(self.config.max_history_records)

        # Load fix options
        for key, var in self.fix_options_vars.items():
            var.set(self.config.default_fix_options.get(key, False))

    def save_settings(self):
        """Save settings to config."""
        self.config.output_directory = self.output_dir_var.get()
        self.config.auto_open_output = self.auto_open_var.get()
        self.config.create_backups = self.create_backups_var.get()
        self.config.save_logs = self.save_logs_var.get()
        self.config.use_fast_mode = self.use_fast_mode_var.get()
        self.config.theme = self.theme_var.get()
        self.config.window_width = self.window_width_var.get()
        self.config.window_height = self.window_height_var.get()
        self.config.keep_history = self.keep_history_var.get()
        self.config.max_history_records = self.max_history_var.get()

        # Save fix options
        for key, var in self.fix_options_vars.items():
            self.config.default_fix_options[key] = var.get()

        # Save to file
        save_config(self.config)

        messagebox.showinfo("Success", "Settings saved successfully!")
        self.window.destroy()

    def reset_defaults(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            from csv_fixer_core import get_default_config
            default_config = get_default_config()

            self.output_dir_var.set(default_config.output_directory)
            self.auto_open_var.set(default_config.auto_open_output)
            self.create_backups_var.set(default_config.create_backups)
            self.save_logs_var.set(default_config.save_logs)
            self.use_fast_mode_var.set(getattr(default_config, 'use_fast_mode', True))
            self.theme_var.set(default_config.theme)
            self.window_width_var.set(default_config.window_width)
            self.window_height_var.set(default_config.window_height)
            self.keep_history_var.set(default_config.keep_history)
            self.max_history_var.set(default_config.max_history_records)

            # Reset fix options
            for key, var in self.fix_options_vars.items():
                var.set(default_config.default_fix_options.get(key, False))


class CSVFixerUnified:
    """Main CSV Fixer application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)

        # Load configuration
        self.config = load_config()

        # Initialize logging
        log_dir = os.path.join(current_dir, "logs")
        init_logging(log_dir)
        self.logger = get_logger()
        self.logger.info("CSV Fixer Unified application starting...")
        self.logger.info(f"Configuration loaded: output_dir={self.config.output_directory}")

        # Initialize history manager
        self.history_manager = HistoryManager()

        # Apply theme
        self.apply_theme()

        # Set window size
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.minsize(800, 600)

        # Create menu bar
        self.create_menu()

        # Create main UI
        self.create_widgets()

        # Bind closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self.show_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Clear History", command=self.clear_history_prompt)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_widgets(self):
        """Create the main UI widgets."""
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_general_tab()
        self.create_batch_tab()
        self.create_timestamp_tab()
        self.create_creator_order_tab()
        self.create_fast_fix_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=10, pady=(0, 10))

    def create_general_tab(self):
        """Create the general CSV fixing tab."""
        # Use padded frame for tab content
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="General Fix")

        # File selection
        file_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(file_frame, text="Select CSV File", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        input_container = ttk.Frame(file_frame, style="Card.TFrame")
        input_container.pack(fill=tk.X)
        
        self.general_file_var = tk.StringVar()
        ttk.Entry(input_container, textvariable=self.general_file_var, font=FONTS["body"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(input_container, text="Browse", command=self.browse_general_file).pack(side=tk.LEFT)

        # Platform Selection (General)
        platform_container = ttk.Frame(file_frame, style="Card.TFrame", padding=(0, 10))
        platform_container.pack(fill=tk.X)
        ttk.Label(platform_container, text="Target Platform Header:").pack(side=tk.LEFT, padx=(0, 10))
        self.general_platform_var = tk.StringVar(value="None")
        general_platform_combo = ttk.Combobox(platform_container, textvariable=self.general_platform_var, values=["None", "TikTok", "Shopee"], state="readonly", width=15)
        general_platform_combo.pack(side=tk.LEFT)

        # Options
        options_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(options_frame, text="Fixing Options", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        options_grid = ttk.Frame(options_frame, style="Card.TFrame")
        options_grid.pack(fill=tk.X)

        self.general_fix_vars = {}
        row = 0
        col = 0
        for i, (key, option) in enumerate(FIX_OPTIONS.items()):
            var = tk.BooleanVar(value=self.config.default_fix_options.get(key, False))
            self.general_fix_vars[key] = var
            ttk.Checkbutton(
                options_grid,
                text=option["name"],
                variable=var,
                style="TCheckbutton"
            ).grid(row=row, column=col, sticky=tk.W, pady=5, padx=10)
            
            col += 1
            if col > 2:
                col = 0
                row += 1

        # Preview area
        preview_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        ttk.Label(preview_frame, text="Preview", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        self.preview_text = tk.Text(preview_frame, height=10, wrap=tk.NONE, font=FONTS["mono"], relief=tk.FLAT, padx=10, pady=10)
        preview_scroll_v = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        preview_scroll_h = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_text.xview)
        self.preview_text.configure(yscrollcommand=preview_scroll_v.set, xscrollcommand=preview_scroll_h.set)

        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        preview_scroll_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Clear", command=self.clear_general).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Preview", command=self.preview_general_file).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Fix CSV", command=self.process_general_file, style="CTA.TButton").pack(side=tk.RIGHT)

    def create_batch_tab(self):
        """Create the batch processing tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="Batch Process")

        # File list
        file_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        ttk.Label(file_frame, text="Files to Process", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        # Listbox with scrollbar
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.batch_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, font=FONTS["body"], relief=tk.FLAT)
        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.batch_listbox.yview)
        self.batch_listbox.configure(yscrollcommand=list_scroll.set)

        self.batch_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # File management buttons
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Add Files", command=self.add_batch_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Add Folder", command=self.add_batch_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove", command=self.remove_batch_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_batch_files).pack(side=tk.LEFT, padx=5)

        # Options
        options_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(options_frame, text="Batch Options", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        options_grid = ttk.Frame(options_frame, style="Card.TFrame")
        options_grid.pack(fill=tk.X)

        self.batch_fix_vars = {}
        row = 0
        col = 0
        for i, (key, option) in enumerate(FIX_OPTIONS.items()):
            var = tk.BooleanVar(value=self.config.default_fix_options.get(key, False))
            self.batch_fix_vars[key] = var
            ttk.Checkbutton(
                options_grid,
                text=option["name"],
                variable=var,
                style="TCheckbutton"
            ).grid(row=row, column=col, sticky=tk.W, pady=5, padx=10)
            
            col += 1
            if col > 2:
                col = 0
                row += 1

        # Output directory
        output_frame = ttk.Frame(options_frame, style="Card.TFrame")
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(output_frame, text="Output Directory:").pack(side=tk.LEFT)
        self.batch_output_var = tk.StringVar(value=self.config.output_directory)
        ttk.Entry(output_frame, textvariable=self.batch_output_var, font=FONTS["body"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Button(output_frame, text="Browse", command=self.browse_batch_output).pack(side=tk.LEFT)

        # Platform Selection (Batch)
        batch_platform_frame = ttk.Frame(options_frame, style="Card.TFrame", padding=(0, 10))
        batch_platform_frame.pack(fill=tk.X)
        ttk.Label(batch_platform_frame, text="Target Platform Header:").pack(side=tk.LEFT, padx=(0, 10))
        self.batch_platform_var = tk.StringVar(value="None")
        batch_platform_combo = ttk.Combobox(batch_platform_frame, textvariable=self.batch_platform_var, values=["None", "TikTok", "Shopee"], state="readonly", width=15)
        batch_platform_combo.pack(side=tk.LEFT)

        # Process button
        ttk.Button(
            tab,
            text="Process All Files",
            command=self.process_batch_files,
            style="CTA.TButton"
        ).pack(side=tk.RIGHT)

    def create_timestamp_tab(self):
        """Create the timestamp fixing tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="Timestamp Fix")

        # File selection
        file_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(file_frame, text="Select CSV File", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        input_container = ttk.Frame(file_frame, style="Card.TFrame")
        input_container.pack(fill=tk.X)
        
        self.timestamp_file_var = tk.StringVar()
        ttk.Entry(input_container, textvariable=self.timestamp_file_var, font=FONTS["body"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(input_container, text="Browse", command=self.browse_timestamp_file).pack(side=tk.LEFT)

        # Options
        options_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(options_frame, text="Timestamp Options", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(options_frame, text="Target Format: BigQuery Compatible (YYYY-MM-DD HH:MM:SS UTC)", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(options_frame, text="Input Formats Detected: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, etc.", font=FONTS["body"]).pack(anchor=tk.W)

        # Process button
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Clear", command=self.clear_timestamp).pack(side=tk.LEFT)
        ttk.Button(
            button_frame,
            text="Fix Timestamps",
            command=self.process_timestamp_file,
            style="CTA.TButton"
        ).pack(side=tk.RIGHT)

    def create_creator_order_tab(self):
        """Create the creator order specific tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="Creator Order")

        # Info label
        info_frame = ttk.Frame(tab, style="Card.TFrame", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            info_frame,
            text="Specialized fixer for Creator Order CSV files with Thai/Unicode data",
            foreground=THEME_COLORS["light"]["primary"],
            font=FONTS["body_bold"],
            background=THEME_COLORS["light"]["card_bg"]
        ).pack()

        # File selection
        file_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(file_frame, text="Select Creator Order CSV File", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        input_container = ttk.Frame(file_frame, style="Card.TFrame")
        input_container.pack(fill=tk.X)
        
        self.creator_file_var = tk.StringVar()
        ttk.Entry(input_container, textvariable=self.creator_file_var, font=FONTS["body"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(input_container, text="Browse", command=self.browse_creator_file).pack(side=tk.LEFT)

        # Features
        features_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        features_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(features_frame, text="Features", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        features = [
            "✓ Sanitizes column names (spaces to underscores)",
            "✓ Converts DD/MM/YYYY timestamps to BigQuery format",
            "✓ Preserves Thai/Unicode characters",
            "✓ Handles creator order specific column structure"
        ]

        for feature in features:
            ttk.Label(features_frame, text=feature, font=FONTS["body"]).pack(anchor=tk.W, pady=2)

        # Process button
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Fix Creator Order CSV",
            command=self.process_creator_file,
            style="CTA.TButton"
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear", command=self.clear_creator).pack(side=tk.LEFT)

    def create_fast_fix_tab(self):
        """Create the fast header fixing tab."""
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="Fast Header Fix")

        # Info label
        info_frame = ttk.Frame(tab, style="Card.TFrame", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            info_frame,
            text="High-speed header replacement for TikTok and Shopee (BigQuery ready)",
            foreground=THEME_COLORS["light"]["primary"],
            font=FONTS["body_bold"],
            background=THEME_COLORS["light"]["card_bg"]
        ).pack()

        # File selection
        file_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(file_frame, text="Select CSV File", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        input_container = ttk.Frame(file_frame, style="Card.TFrame")
        input_container.pack(fill=tk.X)
        
        self.fast_file_var = tk.StringVar()
        ttk.Entry(input_container, textvariable=self.fast_file_var, font=FONTS["body"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(input_container, text="Browse", command=self.browse_fast_file).pack(side=tk.LEFT)

        # Platform selection
        platform_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        platform_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(platform_frame, text="Select Platform", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.fast_platform_var = tk.StringVar(value="tiktok")
        ttk.Radiobutton(platform_frame, text="TikTok", variable=self.fast_platform_var, value="tiktok").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(platform_frame, text="Shopee", variable=self.fast_platform_var, value="shopee").pack(side=tk.LEFT, padx=10)
        
        self.fast_repair_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(platform_frame, text="Repair Rows (Ensures correct column count for BigQuery)", variable=self.fast_repair_var).pack(side=tk.LEFT, padx=20)

        # Features
        features_frame = ttk.Frame(tab, style="Card.TFrame", padding=20)
        features_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(features_frame, text="Why use this?", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(features_frame, text="✓ Replaces headers with BigQuery-compatible English snake_case names", font=FONTS["body"]).pack(anchor=tk.W, pady=2)
        ttk.Label(features_frame, text="✓ Extremely fast (only processes the first line of the file)", font=FONTS["body"]).pack(anchor=tk.W, pady=2)
        ttk.Label(features_frame, text="✓ Safe for very large files (GB+ size)", font=FONTS["body"]).pack(anchor=tk.W, pady=2)

        # Process buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Fast Fix Header",
            command=self.process_fast_file,
            style="CTA.TButton"
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear", command=self.clear_fast).pack(side=tk.LEFT)

    # Menu handlers
    def show_settings(self):
        """Show settings window."""
        SettingsWindow(self.root, self.config)

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            f"{APP_TITLE}\n\n"
            "A comprehensive tool for fixing CSV files\n"
            "for BigQuery compatibility.\n\n"
            "Features:\n"
            "• General CSV fixing\n"
            "• Batch processing\n"
            "• Timestamp format conversion\n"
            "• Creator order specialized fixing\n"
            "• Processing history\n\n"
            "Version 1.0.0"
        )

    def clear_history_prompt(self):
        """Prompt to clear history."""
        if messagebox.askyesno(
            "Clear History",
            "Are you sure you want to clear all processing history?"
        ):
            try:
                count = self.history_manager.clear_history()
                messagebox.showinfo("Success", f"Cleared {count} records from history")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {e}")

    # Tab specific methods
    def browse_general_file(self):
        """Browse for general CSV file."""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=CSV_FILTERS
        )
        if filename:
            self.general_file_var.set(filename)
            self.preview_general_file()

    def preview_general_file(self):
        """Preview the selected CSV file."""
        filename = self.general_file_var.get()
        if not filename or not os.path.exists(filename):
            return

        try:
            # Get file info
            info = get_file_info(filename)

            # Clear preview
            self.preview_text.delete(1.0, tk.END)

            # Show file info
            self.preview_text.insert(tk.END, f"File: {info['name']}\n")
            self.preview_text.insert(tk.END, f"Size: {info['size_formatted']}\n")
            self.preview_text.insert(tk.END, f"Encoding: {info['encoding']}\n")
            self.preview_text.insert(tk.END, f"Columns: {info.get('columns', 'Unknown')}\n")
            self.preview_text.insert(tk.END, f"Rows: {info.get('rows', 'Unknown')}\n")
            self.preview_text.insert(tk.END, "-" * 50 + "\n\n")

            # Show preview of first few rows
            with open(filename, 'r', encoding=info['encoding'], newline='') as f:
                for i, line in enumerate(f):
                    if i >= 5:
                        break
                    self.preview_text.insert(tk.END, line)

            self.status_var.set(f"Preview loaded: {info['name']}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview file: {e}")

    def process_general_file(self):
        """Process the general CSV file."""
        input_file = self.general_file_var.get()
        if not input_file:
            messagebox.showwarning("No File", "Please select a CSV file to process")
            return

        # Get output filename
        output_file = get_output_filename(input_file, self.config.output_directory)

        # Get selected options
        options = {key: var.get() for key, var in self.general_fix_vars.items()}

        # Get selected platform
        platform = self.general_platform_var.get()
        if platform == "None":
            platform = None

        # Process in background
        thread = threading.Thread(
            target=self._process_file_thread,
            args=(input_file, output_file, options, "general", platform)
        )
        thread.daemon = True
        thread.start()

    def _process_file_thread(self, input_file, output_file, options, fixer_type, platform=None):
        """Background thread for processing files."""
        start_time = time.time()
        record = ProcessingRecord(
            input_file=input_file,
            output_file=output_file,
            fixer_type=fixer_type
        )

        # Show progress dialog
        progress = ProgressDialog(self.root, "Processing CSV...")

        try:
            # Ensure output directory exists
            ensure_directory_exists(os.path.dirname(output_file))

            # Process file
            if fixer_type == "creator_order":
                fixes, row_count = process_creator_order_csv(input_file, output_file)
            elif fixer_type.startswith("fast_"):
                platform = fixer_type.split("_")[1]
                repair_rows = options.get('repair_rows', False)
                fixes, row_count = fix_header_only(input_file, output_file, platform, repair_rows=repair_rows)
            else:
                # Check for fast mode
                use_fast = getattr(self.config, 'use_fast_mode', True)
                if use_fast:
                    try:
                        fixes, row_count = process_csv_pandas(input_file, output_file, options, platform=platform)
                        # If pandas fails (e.g. not installed), fallback? 
                        # process_csv_pandas returns error message in fixes if not installed
                        if fixes and fixes[0].startswith("Error: Pandas not installed"):
                            # Fallback to standard
                            fixes, row_count = process_csv_file(input_file, output_file, options, platform=platform)
                    except Exception:
                         # Fallback to standard on any other crash just in case
                         fixes, row_count = process_csv_file(input_file, output_file, options, platform=platform)
                else:
                    fixes, row_count = process_csv_file(input_file, output_file, options, platform=platform)

            # Update record
            record.rows_processed = row_count
            record.fixes_applied = fixes
            record.processing_time = time.time() - start_time
            record.success = True

            # Get file size
            record.file_size = os.path.getsize(input_file)

            # Close progress dialog
            progress.close()

            # Show success message
            messagebox.showinfo(
                "Success",
                f"File processed successfully!\n\n"
                f"Output: {output_file}\n"
                f"Rows processed: {row_count}\n"
                f"Fixes applied: {len(fixes)}"
            )

            # Open output folder if configured
            if self.config.auto_open_output:
                os.startfile(os.path.dirname(output_file))

        except Exception as e:
            record.success = False
            record.error_message = str(e)
            progress.close()
            messagebox.showerror("Error", f"Failed to process file: {e}")

        finally:
            # Save to history
            if self.config.keep_history:
                self.history_manager.add_record(record)

    def clear_general(self):
        """Clear general tab."""
        self.general_file_var.set("")
        self.preview_text.delete(1.0, tk.END)
        self.status_var.set("Ready")

    def add_batch_files(self):
        """Add files to batch list."""
        files = filedialog.askopenfilenames(
            title="Select CSV Files",
            filetypes=CSV_FILTERS
        )
        for file in files:
            if file not in self.batch_listbox.get(0, tk.END):
                self.batch_listbox.insert(tk.END, file)

    def add_batch_folder(self):
        """Add all CSV files from a folder."""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            for file in os.listdir(folder):
                if file.lower().endswith('.csv'):
                    full_path = os.path.join(folder, file)
                    if full_path not in self.batch_listbox.get(0, tk.END):
                        self.batch_listbox.insert(tk.END, full_path)

    def remove_batch_files(self):
        """Remove selected files from batch list."""
        selection = self.batch_listbox.curselection()
        for index in reversed(selection):
            self.batch_listbox.delete(index)

    def clear_batch_files(self):
        """Clear all files from batch list."""
        self.batch_listbox.delete(0, tk.END)

    def browse_batch_output(self):
        """Browse for batch output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.batch_output_var.set(directory)

    def process_batch_files(self):
        """Process all files in batch."""
        files = list(self.batch_listbox.get(0, tk.END))
        if not files:
            messagebox.showwarning("No Files", "Please add files to process")
            return

        output_dir = self.batch_output_var.get()
        if not output_dir:
            messagebox.showwarning("No Output", "Please specify an output directory")
            return

        # Get selected options
        options = {key: var.get() for key, var in self.batch_fix_vars.items()}

        # Log batch processing start
        self.logger.info(f"Starting batch processing of {len(files)} files")
        self.logger.info(f"Output directory: {output_dir}")
        self.logger.info(f"Batch options: {options}")

        # Get selected platform
        platform = self.batch_platform_var.get()
        if platform == "None":
            platform = None

        # Process in background
        thread = threading.Thread(
            target=self._process_batch_thread,
            args=(files, output_dir, options, platform)
        )
        thread.daemon = True
        thread.start()

    def _process_batch_thread(self, files, output_dir, options, platform=None):
        """Background thread for batch processing."""
        progress = ProgressDialog(self.root, "Batch Processing...")
        processed = 0
        failed = 0
        total = len(files)
        start_time = time.time()

        self.logger.info(f"Batch processing thread started for {total} files")

        for i, input_file in enumerate(files):
            if progress.cancelled:
                self.logger.info("Batch processing cancelled by user")
                break

            # Update progress
            progress.update_progress(
                int((i / total) * 100),
                f"Processing {os.path.basename(input_file)}..."
            )

            # Generate output filename
            output_file = get_output_filename(input_file, output_dir)

            # Process file
            record = ProcessingRecord(
                input_file=input_file,
                output_file=output_file,
                fixer_type="batch"
            )

            try:
                self.logger.debug(f"Processing file {i+1}/{total}: {input_file}")
                
                # Check for fast mode
                use_fast = getattr(self.config, 'use_fast_mode', True)
                if use_fast:
                    fixes, row_count = process_csv_pandas(input_file, output_file, options, platform=platform)
                    if fixes and fixes[0].startswith("Error: Pandas not installed"):
                         fixes, row_count = process_csv_file(input_file, output_file, options, platform=platform)
                else:
                    fixes, row_count = process_csv_file(input_file, output_file, options, platform=platform)

                record.rows_processed = row_count
                record.fixes_applied = fixes
                record.success = True
                record.file_size = os.path.getsize(input_file)
                processed += 1

                self.logger.info(f"Successfully processed: {os.path.basename(input_file)}")
                self.logger.debug(f"  - Rows processed: {row_count}")
                self.logger.debug(f"  - Fixes applied: {', '.join(fixes) if fixes else 'None'}")

                # Save to history
                if self.config.keep_history:
                    self.history_manager.add_record(record)

            except Exception as e:
                failed += 1
                record.success = False
                record.error_message = str(e)
                self.logger.error(f"Failed to process {os.path.basename(input_file)}: {str(e)}")
                # Still save to history even if failed
                if self.config.keep_history:
                    self.history_manager.add_record(record)

        progress.close()

        # Calculate total processing time
        total_time = time.time() - start_time
        self.logger.info(f"Batch processing completed in {total_time:.2f} seconds")
        self.logger.info(f"Successfully processed: {processed}, Failed: {failed}")

        messagebox.showinfo(
            "Batch Complete",
            f"Processed {processed} out of {total} files successfully"
        )

        # Open output folder if configured
        if processed > 0 and self.config.auto_open_output:
            self.logger.info(f"Opening output folder: {output_dir}")
            os.startfile(output_dir)

    def browse_timestamp_file(self):
        """Browse for timestamp CSV file."""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=CSV_FILTERS
        )
        if filename:
            self.timestamp_file_var.set(filename)

    def process_timestamp_file(self):
        """Process timestamp file."""
        input_file = self.timestamp_file_var.get()
        if not input_file:
            messagebox.showwarning("No File", "Please select a CSV file")
            return

        output_file = get_output_filename(input_file, self.config.output_directory, "_timestamp_fixed")

        # Process with timestamp fix only
        options = {"timestamps": True}

        thread = threading.Thread(
            target=self._process_file_thread,
            args=(input_file, output_file, options, "timestamp", None)
        )
        thread.daemon = True
        thread.start()

    def clear_timestamp(self):
        """Clear timestamp tab."""
        self.timestamp_file_var.set("")
        self.status_var.set("Ready")

    def browse_creator_file(self):
        """Browse for creator order CSV file."""
        filename = filedialog.askopenfilename(
            title="Select Creator Order CSV File",
            filetypes=CSV_FILTERS
        )
        if filename:
            self.creator_file_var.set(filename)

    def process_creator_file(self):
        """Process creator order file."""
        input_file = self.creator_file_var.get()
        if not input_file:
            messagebox.showwarning("No File", "Please select a creator order CSV file")
            return

        output_file = get_output_filename(input_file, self.config.output_directory, "_creator_fixed")

        thread = threading.Thread(
            target=self._process_file_thread,
            args=(input_file, output_file, {}, "creator_order", None)
        )
        thread.daemon = True
        thread.start()

    def clear_creator(self):
        """Clear creator tab."""
        self.creator_file_var.set("")
        self.status_var.set("Ready")

    def browse_fast_file(self):
        """Browse for fast fix CSV file."""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=CSV_FILTERS
        )
        if filename:
            self.fast_file_var.set(filename)

    def process_fast_file(self):
        """Process file using fast header fix."""
        input_file = self.fast_file_var.get()
        if not input_file:
            messagebox.showwarning("No File", "Please select a CSV file")
            return

        platform = self.fast_platform_var.get()
        repair_rows = self.fast_repair_var.get()
        output_file = get_output_filename(input_file, self.config.output_directory, f"_{platform}_fixed")

        thread = threading.Thread(
            target=self._process_file_thread,
            args=(input_file, output_file, {'repair_rows': repair_rows}, f"fast_{platform}")
        )
        thread.daemon = True
        thread.start()

    def clear_fast(self):
        """Clear fast fix tab."""
        self.fast_file_var.set("")
        self.status_var.set("Ready")

    def apply_theme(self):
        """Apply the selected theme."""
        colors = THEME_COLORS.get(self.config.theme, THEME_COLORS["light"])
        self.root.configure(bg=colors["bg"])

    def on_closing(self):
        """Handle window closing."""
        # Save window size if configured
        if self.config.remember_window_size:
            self.config.window_width = self.root.winfo_width()
            self.config.window_height = self.root.winfo_height()
            save_config(self.config)

        self.root.destroy()

    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    app = CSVFixerUnified()
    app.run()


if __name__ == "__main__":
    main()