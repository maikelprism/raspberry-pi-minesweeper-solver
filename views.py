from events import Events
from minesweeper import Minesweeper
from verify import MinesweeperAI
import pygame
import config

# -----------------------------------------------------------------------------
# Base View Class
# -----------------------------------------------------------------------------
class View:
    """
    Represents a single screen or state in the game (e.g., start menu, game screen).
    This is a base class that all other views inherit from.
    """
    def __init__(self, context):
        """
        Initializes the View.

        Args:
            context: The main GameManager instance, providing access to shared
                     game systems like assets, screen, and event listener.
        """
        self.context = context
        self.language = self.context.language
        self.asset_manager = self.context.asset_manager

        # Load language-specific strings
        if self.language == "EN":
            self.strings = config.STRINGS_ENGLISH
        elif self.language == "DE":
            self.strings = config.STRINGS_GERMAN

    def handle_event(self, event):
        """
        Handles a single game event. To be implemented by subclasses.

        Args:
            event: The event to be processed.
        """
        pass

    def update(self):
        """
        Updates the view's state each frame. To be implemented by subclasses.
        
        This method is responsible for all logic that is not a direct response
        to an event, such as animations or timers.

        Returns:
            The view that should be active in the next frame. If the view
            should not change, it returns `self`.
        """
        return self

    def draw(self):
        """
        Draws the view's contents to the main screen buffer.
        To be implemented by subclasses.
        """
        pass

# -----------------------------------------------------------------------------
# GameView: The main playable screen
# -----------------------------------------------------------------------------
class GameView(View):
    """
    The main playable view of the game, where the user interacts with the
    Minesweeper grid.
    """
    def __init__(self, context):
        """Initializes the GameView, creating the Minesweeper instance and UI elements."""
        super().__init__(context)

        self.clock = pygame.time.Clock()
        # Off-screen drawing surface provided by GameManager
        self.layer0 = self.context.layer0

        # Create the game logic instance
        self.minesweeper = Minesweeper(height=config.FIELD_SIZE[1], width=config.FIELD_SIZE[0], num_mines=self.context.minecount)

        # Mode handling: optionally run AI visualization across board generation attempts
        self.mode = "ai_debug" if getattr(self.context, "ai_debug", False) else "play"
        self._ai_started = False
        if self.mode == "ai_debug":
            # Do not pre-initialize; instead, show every attempt of board generation and AI reasoning
            self.generator = GeneratorDebugger(self.minesweeper)
            # Continuous simulation speed factor (x multiplier). 1.0 is default.
            self.speed_factor = 1.0
            # Prepare translucent overlays
            self._overlay_safe = pygame.Surface((config.CELL_SIZE, config.CELL_SIZE), pygame.SRCALPHA)
            self._overlay_safe.fill((0, 200, 0, 70))
            self._overlay_mine = pygame.Surface((config.CELL_SIZE, config.CELL_SIZE), pygame.SRCALPHA)
            self._overlay_mine.fill((200, 0, 0, 90))
        else:
            # Initialize a solvable board and auto-reveal the first safe cell for a smooth start
            self.minesweeper.init()
            if self.minesweeper.first_safe_move:
                self.minesweeper.reveal_cell(*self.minesweeper.first_safe_move)
                self.minesweeper.selector.selected_pos = self.minesweeper.first_safe_move

        self._init_ui_elements()
        self._load_assets()

        # Calculate total non-mine cells for the progress display
        self.total_safe_cells = (self.minesweeper.width * self.minesweeper.height) - self.minesweeper.num_mines
        self.total_safe_cells_string = str(self.total_safe_cells)

        # Timestamp for when to transition to the fail view after a loss
        self.fail_transition_time = None

    def _init_ui_elements(self):
        """Creates surfaces and calculates offsets for all UI elements."""
        self.cell_size = config.CELL_SIZE
        grid_width_px = self.cell_size * self.minesweeper.width
        grid_height_px = self.cell_size * self.minesweeper.height
        # Store for overlays
        self.grid_width_px = grid_width_px
        self.grid_height_px = grid_height_px

        # Grid surface
        self.grid_surface = pygame.Surface((grid_width_px, grid_height_px))
        self.grid_offset = (
            (self.context.screen.width - grid_width_px) // 2,
            (self.context.screen.height - grid_height_px) // 2,
        )

        # Grid border
        grid_border_background_offset = 30
        grid_border_height = grid_height_px + grid_border_background_offset
        grid_border_width = grid_width_px + grid_border_background_offset
        self.grid_border_offset = (
            (self.context.screen.width - grid_border_width) // 2,
            (self.context.screen.height - grid_border_height) // 2,
        )
        self.grid_border_surface = pygame.Surface((grid_border_width, grid_border_height))

        # AI debug: full-board flash overlays
        if getattr(self, "mode", "play") == "ai_debug":
            self.flash_surface_green = pygame.Surface((grid_width_px, grid_height_px), pygame.SRCALPHA)
            self.flash_surface_green.fill((0, 255, 0, 110))
            self.flash_surface_red = pygame.Surface((grid_width_px, grid_height_px), pygame.SRCALPHA)
            self.flash_surface_red.fill((255, 0, 0, 110))

        # Progress bar
        self.progress_bar_width = grid_width_px / 1.5
        self.progress_bar_height = 40
        self.progress_bar_padding = 10
        progress_bar_surface_height = self.progress_bar_height + self.progress_bar_padding
        progress_bar_surface_width = self.progress_bar_width + self.progress_bar_padding
        self.progress_bar_offset = (
            (self.context.screen.width - progress_bar_surface_width) // 2,
            self.context.screen.height - ((self.context.screen.height - grid_height_px) // 4) - 20,
        )
        self.progress_bar_surface = pygame.Surface((progress_bar_surface_width, progress_bar_surface_height))

        # Text offsets
        self.progress_bar_label_center = (self.context.screen.width // 2, self.progress_bar_offset[1] - 15)
        self.progress_bar_percent_center = (progress_bar_surface_width // 2, progress_bar_surface_height // 2)
        self.title_center = (self.context.screen.width // 2, ((self.context.screen.height - grid_height_px) // 4) - 10)

    def _load_assets(self):
        """Loads fonts and images needed for this view."""
        self.font_regular = self.asset_manager.get_font("regular")
        self.font_title = self.asset_manager.get_font("title")
        self.font_subtext = self.asset_manager.get_font("subtext")

        self.image_crosshair = self.asset_manager.get_image("crosshair")
        self.image_asteroid = self.asset_manager.get_image("asteroid")
        self.image_background = self.asset_manager.get_image("background")

        self.outline_color = config.Color.CELL_OUTLINE.value
        self.cell_background_color = config.Color.DARK_BLUE.value
        
    def handle_event(self, event):
        """Handles user input for navigating and interacting with the grid."""
        # In AI debug mode, allow pause/resume, single-step, and continuous speed controls
        if getattr(self, "mode", "play") == "ai_debug":
            if event == Events.BUTTON_ENTER:
                # Toggle pause
                if hasattr(self, "generator"):
                    self.generator.paused = not getattr(self.generator, "paused", False)
                return
            if event == Events.BUTTON_RIGHT:
                # Manual single step only when paused
                if hasattr(self, "generator") and getattr(self.generator, "paused", False):
                    done = self.generator.step_manual()
                    if done:
                        if self.minesweeper.first_safe_move:
                            self.minesweeper.reveal_cell(*self.minesweeper.first_safe_move)
                            self.minesweeper.selector.selected_pos = self.minesweeper.first_safe_move
                        self.mode = "play"
                return
            # Dynamic continuous speed control with Up/Down arrows while in AI debug mode
            if event == Events.BUTTON_UP:
                # Increase speed by 25% per press, clamp to a reasonable max
                self.speed_factor = min(self.speed_factor * 1.25, 250.0)
                self._apply_sim_speed()
                return
            if event == Events.BUTTON_DOWN:
                # Decrease speed by 20% per press (inverse of 1.25), clamp to a reasonable min
                self.speed_factor = max(self.speed_factor / 1.25, 0.10)
                self._apply_sim_speed()
                return
        if self.minesweeper.is_game_over:
            return # Do not handle input if the game is over

        selected_cell = self.minesweeper.selector.selected_pos

        if event == Events.BUTTON_UP:
            self.minesweeper.selector.move(-1, 0)
        elif event == Events.BUTTON_DOWN:
            self.minesweeper.selector.move(1, 0)
        elif event == Events.BUTTON_RIGHT:
            self.minesweeper.selector.move(0, 1)
        elif event == Events.BUTTON_LEFT:
            self.minesweeper.selector.move(0, -1)
        elif event == Events.BUTTON_FLAG:
            self.minesweeper.flag_cell(*selected_cell)
        elif event == Events.BUTTON_ENTER:
            self.minesweeper.reveal_cell(*selected_cell)
            # If the move ends the game, set up the transition state
            if self.minesweeper.is_game_over and not self.minesweeper.is_win:
                self.outline_color = config.Color.RED.value
                self.cell_background_color = config.Color.DARK_RED.value
                self.fail_transition_time = pygame.time.get_ticks() + config.GAME_OVER_RESET_DELAY
                    
    def update(self):
        """
        Updates the game state, checking for win/loss conditions and handling
        view transitions.
        """
        # Drive AI visualization across board attempts until a solvable board is confirmed, then switch to play
        if self.mode == "ai_debug":
            if not self._ai_started:
                self.generator.start()
                self._ai_started = True
            # When paused, do not auto-advance
            done = False
            if not getattr(self.generator, "paused", False):
                done = self.generator.step()
            if done:
                # We now have a solvable board active in self.minesweeper
                if self.minesweeper.first_safe_move:
                    self.minesweeper.reveal_cell(*self.minesweeper.first_safe_move)
                    self.minesweeper.selector.selected_pos = self.minesweeper.first_safe_move
                self.mode = "play"
            return self

        if self.minesweeper.is_game_over:
            if self.minesweeper.is_win:
                return GGView(self.context) # Transition to win screen
            
            # If lost, wait for a delay before transitioning to the fail screen
            if self.fail_transition_time and pygame.time.get_ticks() > self.fail_transition_time:
                return FailView(self.context)
        
        return self # No view change

    def draw(self):
        """Draws the entire game screen, including the grid and UI elements."""
        # Calculate the percentage for progress bar
        if getattr(self, "mode", "play") == "ai_debug":
            ai_dbg = getattr(self.generator, "ai_dbg", None)
            revealed_count = len(ai_dbg.ai.moves_made) if ai_dbg else 0
        else:
            revealed_count = self.minesweeper.revealed_safe_cells
        percent_finished = (revealed_count / self.total_safe_cells) if self.total_safe_cells > 0 else 0

        self.layer0.fill(config.Color.BLACK.value)
        self.layer0.blit(self.image_background, (0, 0))

        self._draw_progress_bar(percent_finished)
        self._draw_grid()
        self._draw_ui_text(percent_finished, revealed_count)
        if getattr(self, "mode", "play") == "ai_debug":
            self._draw_ai_debug_hud()
        
        self.clock.tick(60)

    def _draw_grid(self):
        """Draws the Minesweeper grid and its border."""
        # Draw frame
        self.grid_border_surface.fill(self.outline_color)
        self.layer0.blit(self.grid_border_surface, self.grid_border_offset)

        # Draw all cells
        for row in self.minesweeper.cells:
            for cell in row:
                self._draw_cell(cell)
        # AI debug flash overlay on the grid surface
        if getattr(self, "mode", "play") == "ai_debug":
            gen = getattr(self, "generator", None)
            if gen and gen.flash_active:
                overlay = self.flash_surface_green if gen.flash_color == "green" else self.flash_surface_red
                self.grid_surface.blit(overlay, (0, 0))
        
        self.layer0.blit(self.grid_surface, self.grid_offset)

    

    def _draw_progress_bar(self, percent_finished):
        """Draws the progress bar and its fill."""
        self.progress_bar_surface.fill(self.outline_color)
        progress_bar_rect = pygame.Rect(
            self.progress_bar_padding // 2, 
            self.progress_bar_padding // 2, 
            self.progress_bar_width * percent_finished, 
            self.progress_bar_height
        )
        pygame.draw.rect(self.progress_bar_surface, config.Color.WHITE.value, progress_bar_rect)
        self.layer0.blit(self.progress_bar_surface, self.progress_bar_offset)

    def _draw_ui_text(self, percent_finished, revealed_count):
        """Draws all text elements like the title and progress indicators."""
        # Revealed cells text
        revealed_text = f"{self.strings['revealed']} {revealed_count} / {self.total_safe_cells_string}"
        text_revealed = self.font_regular.render(revealed_text, True, config.Color.WHITE.value)
        text_revealed_rect = text_revealed.get_rect(center=self.progress_bar_label_center)

        # Progress bar percentage text
        percent_text = f"{int(percent_finished * 100)}%"
        text_percent = self.font_regular.render(percent_text, True, config.Color.BLACK.value)
        percent_rect = text_percent.get_rect(center=self.progress_bar_percent_center)

        # Game title (hidden in AI debug mode to make room for debug HUD)
        draw_title = getattr(self, "mode", "play") != "ai_debug"
        if draw_title:
            text_title = self.font_title.render(config.GAME_TITLE, True, config.Color.WHITE.value)
            title_rect = text_title.get_rect(center=self.title_center)

        # Blit text to surfaces
        self.progress_bar_surface.blit(text_percent, percent_rect)
        self.layer0.blit(text_revealed, text_revealed_rect)
        if draw_title:
            self.layer0.blit(text_title, title_rect)

    def _draw_cell(self, cell):
        """
        Draws a single cell based on its state (hidden, revealed, flagged).

        Args:
            cell: The Cell object to draw.
        """
        rect = pygame.Rect(cell.col * self.cell_size, cell.row * self.cell_size, self.cell_size, self.cell_size)

        # Draw cell background
        self.grid_surface.fill(self.cell_background_color, rect)

        # Draw content based on state or AI debug overlays
        if getattr(self, "mode", "play") == "ai_debug":
            ai_dbg = getattr(self.generator, "ai_dbg", None)
            pos = (cell.row, cell.col)
            if ai_dbg:
                # Mines inferred by AI
                if pos in ai_dbg.ai.mines:
                    img_rect = self.image_asteroid.get_rect(center=rect.center)
                    self.grid_surface.blit(self.image_asteroid, img_rect)
                    self.grid_surface.blit(self._overlay_mine, rect)
                # Moves made (revealed safes in AI reasoning)
                elif pos in ai_dbg.ai.moves_made:
                    num_text = self.font_regular.render(str(cell.adjacent_mines), True, config.Color.WHITE.value)
                    num_rect = num_text.get_rect(center=rect.center)
                    self.grid_surface.blit(num_text, num_rect)
                # Known safes not yet moved to
                elif pos in ai_dbg.ai.safes:
                    self.grid_surface.blit(self._overlay_safe, rect)
        else:
            if cell.is_flagged:
                img_rect = self.image_crosshair.get_rect(center=rect.center)
                self.grid_surface.blit(self.image_crosshair, img_rect)
            elif cell.is_revealed:
                if cell.is_mine:
                    img_rect = self.image_asteroid.get_rect(center=rect.center)
                    self.grid_surface.blit(self.image_asteroid, img_rect)
                else:
                    # Draw the number of adjacent mines
                    num_text = self.font_regular.render(str(cell.adjacent_mines), True, config.Color.WHITE.value)
                    num_rect = num_text.get_rect(center=rect.center)
                    self.grid_surface.blit(num_text, num_rect)
        
        # Draw cell outline (red for selected, default otherwise)
        outline_color = config.Color.RED.value if self.minesweeper.selector.selected_pos == (cell.row, cell.col) else self.outline_color
        pygame.draw.rect(self.grid_surface, outline_color, rect, width=1)

    def _draw_ai_debug_hud(self):
        """Draws AI debug info as four separate, fixed-position metrics to avoid jitter."""
        ai_dbg = getattr(self.generator, "ai_dbg", None)
        sf = getattr(self, 'speed_factor', 1.0)

        attempt_num = self.generator.attempt
        safe_moves_remaining = 0
        mines_found = 0
        if ai_dbg:
            safe_moves_remaining = max(0, len(ai_dbg.ai.safes - ai_dbg.ai.moves_made))
            mines_found = len(ai_dbg.ai.mines)

        total_mines = self.minesweeper.num_mines

        # Prepare individual metric strings
        text_attempt = f"Attempt {attempt_num}"
        text_safes = f"Safe moves {safe_moves_remaining}"
        text_mines = f"Mines {mines_found}/{total_mines}"
        text_speed = f"Speed x{sf:.2f}"

        # Layout: split the grid width into four equal slots and left-anchor each metric in its slot.
        grid_left = self.grid_offset[0]
        grid_width = self.grid_width_px
        slots = 4
        slot_w = max(1, grid_width // slots)
        y = self.title_center[1] - self.font_subtext.get_height() // 2

        metrics = [text_attempt, text_safes, text_mines, text_speed]
        for i, txt in enumerate(metrics):
            surf = self.font_subtext.render(txt, True, config.Color.WHITE.value)
            x = grid_left + i * slot_w
            self.layer0.blit(surf, (x, y))

    def _apply_sim_speed(self):
        if not hasattr(self, 'generator'):
            return
        # Base timings at speed_factor == 1.0 (roughly old tier 3)
        base_step = 180
        base_attempt_pause = 250
        base_flash = 220
        base_post_flash = 220
        sf = max(0.1, min(getattr(self, 'speed_factor', 1.0), 250.0))

        # Scale timings inversely with speed factor, with minimum floors
        step_delay = max(1, int(round(base_step / sf)))
        attempt_pause = max(20, int(round(base_attempt_pause / sf)))
        flash = max(20, int(round(base_flash / sf)))
        post_flash = max(20, int(round(base_post_flash / sf)))

        # Apply new timings to generator
        gen = self.generator
        gen.step_delay_ms = step_delay
        gen.attempt_pause_ms = attempt_pause
        gen.flash_duration_ms = flash
        gen.post_flash_pause_ms = post_flash

        # If there's an active AI stepper, update its pacing too
        if getattr(gen, 'ai_dbg', None) is not None:
            gen.ai_dbg.step_delay_ms = step_delay

        # Recalculate the next tick immediately based on current phase
        if not getattr(gen, 'paused', False):
            now = pygame.time.get_ticks()
            if gen._phase == "attempt":
                # Respect AI stepper if present
                if getattr(gen, 'ai_dbg', None) is not None:
                    gen.ai_dbg._next_tick = now + step_delay
                gen._next_tick = now + step_delay
            elif gen._phase == "flashing":
                gen._next_tick = now + flash
            elif gen._phase == "post_pause":
                gen._next_tick = now + post_flash
            else:
                # Not started yet or unknown phase: use attempt pause
                gen._next_tick = now + attempt_pause


class AIDebugger:
    """Simple stepper to visualize MinesweeperAI reasoning on the current board."""
    def __init__(self, minesweeper, step_delay_ms=120):
        self.ms = minesweeper
        self.ai = MinesweeperAI(width=self.ms.width, height=self.ms.height)
        self.started = False
        self.done = False
        self.step_delay_ms = step_delay_ms
        self._next_tick = 0

    def start(self):
        if self.started:
            return
        if not self.ms.first_safe_move:
            self.done = True
            return
        first = self.ms.first_safe_move
        first_cell = self.ms.cells[first[0]][first[1]]
        # Seed constraints with the first revealed clue
        self.ai.add_constraint(first, first_cell.adjacent_mines)
        # Highlight the first considered cell in the UI selection
        self.ms.selector.selected_pos = first
        self.started = True
        self._next_tick = pygame.time.get_ticks() + self.step_delay_ms

    def step(self):
        """Advance AI by one safe move step according to delay. Returns True if finished."""
        if self.done or not self.started:
            return self.done
        now = pygame.time.get_ticks()
        if now < self._next_tick:
            return False

        # Determine next safe move not yet explored
        safe_moves = self.ai.safes - self.ai.moves_made
        if safe_moves:
            move = next(iter(safe_moves))
            self.ai.moves_made.add(move)
            cell = self.ms.cells[move[0]][move[1]]
            self.ai.add_constraint(move, cell.adjacent_mines)
            # Update the game selector to point at the most recently evaluated cell
            self.ms.selector.selected_pos = move
            self._next_tick = now + self.step_delay_ms
            return False

        # No more safe moves -> finish visualization phase
        self.done = True
        return True


class GeneratorDebugger:
    """Drives repeated board generation attempts and visualizes AI reasoning until a solvable board is found."""
    def __init__(self, minesweeper, step_delay_ms=120, attempt_pause_ms=100, flash_duration_ms=200, post_flash_pause_ms=200):
        self.ms = minesweeper
        self.step_delay_ms = step_delay_ms
        self.attempt_pause_ms = attempt_pause_ms
        self.flash_duration_ms = flash_duration_ms
        self.post_flash_pause_ms = post_flash_pause_ms
        self.started = False
        self.done = False
        self.attempt = 0
        self.ai_dbg = None
        self._next_tick = 0
        # Flash state
        self.flash_active = False
        self.flash_color = None  # "green" or "red"
        self._phase = None  # None | "attempt" | "flashing" | "post_pause"
        self._result_solved = False
        # Pause state
        self.paused = False

    def start(self):
        if self.started:
            return
        self.started = True
        self._start_new_attempt()

    def _start_new_attempt(self):
        # Reset basic state on the Minesweeper model
        self.ms.is_game_over = False
        self.ms.is_win = False
        self.ms.selector.selected_pos = (0, 0)
        # Generate a fresh board and find a seed safe move
        self.ms._generate_board()
        self.ms._find_first_safe_move()
        self.attempt += 1
        self.ai_dbg = None
        self._phase = "attempt"
        self.flash_active = False
        self.flash_color = None
        self._result_solved = False
        self._next_tick = pygame.time.get_ticks() + self.attempt_pause_ms

    def step(self):
        if self.done or not self.started:
            return self.done
        if self.paused:
            return False
        now = pygame.time.get_ticks()
        if now < self._next_tick:
            return False

        # Phase handling
        if self._phase == "attempt":
            # Initialize AI for this attempt if needed
            if not self.ai_dbg:
                if not self.ms.first_safe_move:
                    # Degenerate case; start a new attempt immediately
                    self._start_new_attempt()
                    return False
                self.ai_dbg = AIDebugger(self.ms, step_delay_ms=self.step_delay_ms)
                self.ai_dbg.start()
                self._next_tick = now + self.step_delay_ms
                return False
            # Advance AI reasoning
            finished_attempt = self.ai_dbg.step()
            if finished_attempt:
                total_safe = self.ms.width * self.ms.height - self.ms.num_mines
                self._result_solved = (len(self.ai_dbg.ai.moves_made) == total_safe)
                # Start flash
                self.flash_active = True
                self.flash_color = "green" if self._result_solved else "red"
                self._phase = "flashing"
                self._next_tick = now + self.flash_duration_ms
                return False
            # Continue attempt
            self._next_tick = now + self.step_delay_ms
            return False

        if self._phase == "flashing":
            # End flash -> enter post pause
            self.flash_active = False
            self._phase = "post_pause"
            self._next_tick = now + self.post_flash_pause_ms
            return False

        if self._phase == "post_pause":
            if self._result_solved:
                self.done = True
                return True
            # If not solved, start a new attempt
            self._start_new_attempt()
            return False

        # Fallback: reset to new attempt
        self._start_new_attempt()
        return False

    def step_manual(self):
        """Advance a single step ignoring time delays (used when paused). Returns True if finished."""
        if self.done or not self.started:
            return self.done
        # Do not respect self.paused here; manual stepping requires paused by caller
        if self._phase == "attempt":
            if not self.ai_dbg:
                if not self.ms.first_safe_move:
                    self._start_new_attempt()
                    return False
                self.ai_dbg = AIDebugger(self.ms, step_delay_ms=self.step_delay_ms)
                self.ai_dbg.start()
                return False
            finished_attempt = self.ai_dbg.step()
            if finished_attempt:
                total_safe = self.ms.width * self.ms.height - self.ms.num_mines
                self._result_solved = (len(self.ai_dbg.ai.moves_made) == total_safe)
                self.flash_active = True
                self.flash_color = "green" if self._result_solved else "red"
                self._phase = "flashing"
                return False
            return False
        if self._phase == "flashing":
            self.flash_active = False
            self._phase = "post_pause"
            return False
        if self._phase == "post_pause":
            if self._result_solved:
                self.done = True
                return True
            self._start_new_attempt()
            return False
        self._start_new_attempt()
        return False

# -----------------------------------------------------------------------------
# GGView: The "Good Game" / Win Screen
# -----------------------------------------------------------------------------
class GGView(View):
    """
    The view that is shown when the player has successfully won the game.
    """
    def __init__(self, context):
        """Initializes the win screen view."""
        super().__init__(context)
      
        self.text = self.asset_manager.get_font("title").render(self.strings["mission_success"], True, config.Color.WHITE.value)
        self.subtext = self.asset_manager.get_font("subtext").render(self.strings["trajectory_restored"], True, config.Color.WHITE.value)
        
        center_screen = self.context.screen.get_center()
        self.text_rect = self.text.get_rect(center=center_screen)
        self.subtext_rect = self.subtext.get_rect(center=(center_screen[0], center_screen[1] + 100))
    
    def draw(self):
        """Draws the win message."""
        self.context.layer0.fill(config.Color.BLACK.value)
        self.context.layer0.blit(self.text, self.text_rect)
        self.context.layer0.blit(self.subtext, self.subtext_rect)

# -----------------------------------------------------------------------------
# StartView: The initial screen of the game
# -----------------------------------------------------------------------------
class StartView(View):
    """
    The initial view shown when the game starts, prompting the user to begin.
    """
    def __init__(self, context):
        """Initializes the start screen view."""
        super().__init__(context)
        self.next_view = None

        self.text = self.asset_manager.get_font("title").render(self.strings["critical_error"], True, config.Color.RED.value)
        self.subtext = self.asset_manager.get_font("subtext").render(self.strings["enter_prompt"], True, config.Color.WHITE.value)
        
        center_screen = self.context.screen.get_center()
        self.text_rect = self.text.get_rect(center=center_screen)
        self.subtext_rect = self.subtext.get_rect(center=(center_screen[0], center_screen[1] + 100))

    def handle_event(self, event):
        """Transitions to the main game view when the Enter button is pressed."""
        if event == Events.BUTTON_ENTER:
            self.next_view = GameView(self.context)
    
    def update(self):
        """
        Checks if a view transition is pending and returns the next view.
        """
        return self.next_view if self.next_view else self

    def draw(self):
        """Draws the start message."""
        self.context.layer0.fill(config.Color.BLACK.value)
        self.context.layer0.blit(self.text, self.text_rect)
        self.context.layer0.blit(self.subtext, self.subtext_rect)

# -----------------------------------------------------------------------------
# FailView: The screen shown after losing, before a reset
# -----------------------------------------------------------------------------
class FailView(View):
    """
    A timed view shown after the player loses. After a countdown, it
    transitions back to a new game.
    """
    def __init__(self, context):
        """Initializes the fail screen view and its timer."""
        super().__init__(context)
        
        self.start_ticks = pygame.time.get_ticks()
        self.timer_length = config.FAIL_VIEW_TIMER_LENGTH
        self.next_view = self

    def update(self):
        """
        Checks the timer and transitions back to the game view when it expires.
        """
        elapsed_seconds = (pygame.time.get_ticks() - self.start_ticks) // 1000
        if elapsed_seconds >= self.timer_length:
            self.next_view = GameView(self.context)
        return self.next_view

    def draw(self):
        """Draws the countdown timer."""
        self.context.layer0.fill(config.Color.BLACK.value)
        
        remaining_seconds = self.timer_length - ((pygame.time.get_ticks() - self.start_ticks) // 1000)
        timer_text_str = f"{remaining_seconds} {self.strings['seconds']}"
        
        timer_text = self.asset_manager.get_font("title").render(timer_text_str, True, config.Color.WHITE.value)
        subtext = self.asset_manager.get_font("subtext").render(self.strings["until_reset"], True, config.Color.WHITE.value)

        center_screen = self.context.screen.get_center()
        timer_text_rect = timer_text.get_rect(center=center_screen)
        subtext_rect = subtext.get_rect(center=(center_screen[0], center_screen[1] + 100))
        
        self.context.layer0.blit(timer_text, timer_text_rect)
        self.context.layer0.blit(subtext, subtext_rect)

# -----------------------------------------------------------------------------
# EmptyView: A blank screen for clean shutdown
# -----------------------------------------------------------------------------
class EmptyView(View):
    """
    A completely blank view, used to clear the screen before quitting the game.
    """
    def __init__(self, context):
        """Initializes the empty view."""
        super().__init__(context)

    def draw(self):
        """Draws a black screen."""
        self.context.layer0.fill(config.Color.BLACK.value)




