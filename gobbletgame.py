'''Added docstrings for classes and reduce line sizes'''
import sys
from enum import Enum, auto
from typing import List, Optional
# pylint: disable=no-member
import pygame
from pygame import SRCALPHA
from pygame.locals import QUIT, MOUSEBUTTONDOWN

# Initialize pygame
pygame.init()  # pylint: disable=no-member

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BOARD_SIZE = 3
CELL_SIZE = 120
BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE * CELL_SIZE) // 2
BOARD_OFFSET_Y = 100
PIECE_SIZES = [60, 40, 20]  # Large, Medium, Small radii
PIECE_COLORS = [(255, 0, 0), (255, 255, 0)]  # Red, Yellow
BACKGROUND_COLOR = (240, 240, 240)
GRID_COLOR = (50, 50, 50)
INFO_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (100, 200, 255, 100)

# Game states
class GameState(Enum):
    '''Game States'''
    PLAYING = auto()
    RED_WINS = auto()
    YELLOW_WINS = auto()
    DRAW = auto()

class Player(Enum):
    '''Class for Players'''
    RED = 0
    YELLOW = 1

class Piece:
    '''Class for Pieces'''
    def __init__(self, player: Player, size: int):
        self.player = player
        self.size = size  # 0 for large, 1 for medium, 2 for small
        self.x = 0
        self.y = 0
        self.on_board = False
        self.visible = True

    def draw(self, surface):
        '''Draws the piece'''
        radius = PIECE_SIZES[self.size]
        color = PIECE_COLORS[self.player.value]
        pygame.draw.circle(surface, color, (self.x, self.y), radius)
        pygame.draw.circle(surface, GRID_COLOR, (self.x, self.y), radius, 2)

class Cell:
    '''Class for Cells'''
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self.x = BOARD_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
        self.y = BOARD_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
        self.pieces: List[Piece] = []

    def add_piece(self, piece: Piece):
        '''Place piece on top (it gobbles any smaller pieces underneath)'''
        piece.x = self.x
        piece.y = self.y
        piece.on_board = True

        for p in self.pieces:
            p.visible = False

        self.pieces.append(piece)
        piece.visible = True

    def remove_piece(self, piece: Piece):
        '''Remove piece from the cell'''
        if piece in self.pieces:
            self.pieces.remove(piece)
            # Update visibility of the top piece if any remain
            if self.pieces:
                self.pieces[-1].visible = True

    def top_piece(self) -> Optional[Piece]:
        '''Return the topmost piece in the cell'''
        return self.pieces[-1] if self.pieces else None

    def can_place_piece(self, piece: Piece) -> bool:
        '''Check if the piece can be placed in the cell'''
        if not self.pieces:
            return True
        top = self.top_piece()
        return piece.size < top.size  # Can only gobble smaller pieces

    def draw(self, surface):
        '''Draws cell'''
        pygame.draw.rect(surface, GRID_COLOR, (
            BOARD_OFFSET_X + self.col * CELL_SIZE,
            BOARD_OFFSET_Y + self.row * CELL_SIZE,
            CELL_SIZE, CELL_SIZE
        ), 2)
        for piece in self.pieces:
            if piece.visible:
                piece.draw(surface)

class Board:
    '''Class for Board'''
    def __init__(self):
        self.cells = [[Cell(row, col) for col in range(BOARD_SIZE)] for row in range(BOARD_SIZE)]
        self.history = []  # For rewind feature

    def get_cell(self, row: int, col: int) -> Cell:
        '''Simply return cell at given row and column'''
        return self.cells[row][col]

    def get_cell_at_position(self, x: int, y: int) -> Optional[Cell]:
        '''Return the cell at the given position'''
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell_x = BOARD_OFFSET_X + col * CELL_SIZE
                cell_y = BOARD_OFFSET_Y + row * CELL_SIZE
                if (cell_x <= x < cell_x + CELL_SIZE and
                    cell_y <= y < cell_y + CELL_SIZE):
                    return self.get_cell(row, col)
        return None

    def check_win(self, last_move_cell: Cell) -> Optional[Player]:
        '''Check if the last move created a winning sequence'''

        visible_pieces = []
        for row in range(BOARD_SIZE):
            row_pieces = []
            for col in range(BOARD_SIZE):
                cell = self.get_cell(row, col)
                if cell.pieces and cell.pieces[-1].visible:
                    row_pieces.append(cell.pieces[-1])
                else:
                    row_pieces.append(None)
            visible_pieces.append(row_pieces)

        # Check for 3 in a row for both players
        for player in [Player.RED, Player.YELLOW]:
            # Check rows
            for row in range(BOARD_SIZE):
                if all(piece and piece.player == player for piece in visible_pieces[row]):
                    return player

            # Check columns
            for col in range(BOARD_SIZE):
                if all(visible_pieces[row][col] and visible_pieces[row][col].player == player
                       for row in range(BOARD_SIZE)):
                    return player

            # Check diagonals
            if all(visible_pieces[i][i] and visible_pieces[i][i].player == player
                   for i in range(BOARD_SIZE)):
                return player
            if all(visible_pieces[i][BOARD_SIZE-1-i] and
                    visible_pieces[i][BOARD_SIZE-1-i].player == player
                   for i in range(BOARD_SIZE)):
                return player
        return None
    def draw(self, surface):
        '''Draw board outline'''
        pygame.draw.rect(surface, GRID_COLOR, (
            BOARD_OFFSET_X, BOARD_OFFSET_Y,
            CELL_SIZE * BOARD_SIZE, CELL_SIZE * BOARD_SIZE
        ), 3)

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                self.get_cell(row, col).draw(surface)

    def save_state(self):
        '''Save current board state for rewind feature'''
        state = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = self.get_cell(row, col)
                state.append([{
                    'player': piece.player.value,
                    'size': piece.size,
                    'visible': piece.visible
                } for piece in cell.pieces])
        self.history.append(state)

class GobbletGame:
    '''Class for Gobblet Game'''
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gobblet Game")
        self.clock = pygame.time.Clock()

        # Initialize fonts properly
        self.font = pygame.font.Font(None, 36)

        self.board = Board()
        self.state = GameState.PLAYING
        self.current_player = Player.RED

        # Initialize pieces for both players (2 of each size)
        self.reserve_pieces = {
            Player.RED: [],
            Player.YELLOW: []
        }

        for player in [Player.RED, Player.YELLOW]:
            for size in range(3):  # 0=large, 1=medium, 2=small
                for _ in range(2):  # 2 of each size
                    self.reserve_pieces[player].append(Piece(player, size))
        # Set initial positions for reserve pieces
        self.update_reserve_positions()
        self.selected_piece = None
        self.original_cell = None
    def update_reserve_positions(self):
        '''Position pieces in the reserve areas on the left and right'''
        for player in [Player.RED, Player.YELLOW]:
            x_base = 50 if player == Player.RED else SCREEN_WIDTH - 50
            y_base = 200
            off_board_pieces = [p for p in self.reserve_pieces[player] if not p.on_board]
            for size in range(3):
                pieces_of_size = [p for p in off_board_pieces if p.size == size]
                for i, piece in enumerate(pieces_of_size):
                    offset = i * 40
                    piece.x = x_base + (20 if player == Player.YELLOW else -20) * i
                    piece.y = y_base + size * 70 + offset
    def handle_click(self, x: int, y: int):
        '''Handle mouse click events'''
        if self.state != GameState.PLAYING:
            self.reset_game()
            return
        # Handle piece selection or placement
        if self.selected_piece:
            # We have a piece selected, try to place it
            target_cell = self.board.get_cell_at_position(x, y)
            if target_cell:
                if self.original_cell == target_cell:
                    # Clicked on the same cell, deselect
                    self.selected_piece = None
                    self.original_cell = None
                    return
                if target_cell.can_place_piece(self.selected_piece):
                    # Save state for rewind
                    self.board.save_state()
                    # Remove from original cell if on board
                    if self.original_cell:
                        self.original_cell.remove_piece(self.selected_piece)
                    # Add to new cell
                    target_cell.add_piece(self.selected_piece)
                    # Check for win condition
                    winner = self.board.check_win(target_cell)
                    if winner == Player.RED:
                        self.state = GameState.RED_WINS
                    elif winner == Player.YELLOW:
                        self.state = GameState.YELLOW_WINS
                    else:
                        # Switch players
                        if self.current_player == Player.RED:
                            self.current_player = Player.YELLOW
                        else:
                            self.current_player = Player.RED
                    # Reset selection
                    self.selected_piece = None
                    self.original_cell = None
                    # Update reserve positions
                    self.update_reserve_positions()
            else:
                # Clicked outside the board, deselect
                self.selected_piece = None
                self.original_cell = None
        else:
            # No piece selected yet, try to select one
            # First check board pieces
            cell = self.board.get_cell_at_position(x, y)
            if cell and cell.pieces and cell.top_piece().player == self.current_player:
                self.selected_piece = cell.top_piece()
                self.original_cell = cell
                return
            # Then check reserve pieces
            for piece in self.reserve_pieces[self.current_player]:
                if (not piece.on_board and
                    (piece.x-PIECE_SIZES[piece.size] <= x <= piece.x + PIECE_SIZES[piece.size]) and
                    (piece.y-PIECE_SIZES[piece.size] <= y <= piece.y + PIECE_SIZES[piece.size])):
                    self.selected_piece = piece
                    self.original_cell = None
                    return
    def reset_game(self):
        '''Reset the game state'''
        self.board = Board()
        self.state = GameState.PLAYING
        self.current_player = Player.RED
        # Reset pieces
        self.reserve_pieces = {
            Player.RED: [],
            Player.YELLOW: []
        }
        for player in [Player.RED, Player.YELLOW]:
            for size in range(3):
                for _ in range(2):
                    self.reserve_pieces[player].append(Piece(player, size))
        self.update_reserve_positions()
        self.selected_piece = None
        self.original_cell = None
    def draw(self):
        '''Draw the game state'''
        self.screen.fill(BACKGROUND_COLOR)
        # Draw the board
        self.board.draw(self.screen)
        # Draw reserve pieces
        for player in [Player.RED, Player.YELLOW]:
            for piece in self.reserve_pieces[player]:
                if not piece.on_board:
                    piece.draw(self.screen)
        # Draw highlight for selected piece
        if self.selected_piece:
            radius = PIECE_SIZES[self.selected_piece.size] + 5
            highlight_surface = pygame.Surface((radius*2, radius*2), SRCALPHA)
            pygame.draw.circle(highlight_surface, HIGHLIGHT_COLOR, (radius, radius), radius)
            xrad = self.selected_piece.x - radius
            yrad = self.selected_piece.y - radius
            self.screen.blit(highlight_surface, (xrad , yrad))
        # Draw current player indicator
        color_name = "RED" if self.current_player == Player.RED else "YELLOW"
        val = self.current_player.value
        text = self.font.render(f"Current Player: {color_name}", True, PIECE_COLORS[val])
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 30))
        if self.state == GameState.RED_WINS:
            rval = Player.RED.value
            text = self.font.render("RED WINS! Click to play again", True, PIECE_COLORS[rval])
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 550))
        elif self.state == GameState.YELLOW_WINS:
            yelval = Player.YELLOW.value
            text = self.font.render("YELLOW WINS! Click to play again", True, PIECE_COLORS[yelval])
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 550))
    def run(self):
        '''Main game loop'''
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                    # Left mouse button clicked
                    self.handle_click(*event.pos)
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GobbletGame()
    game.run()
