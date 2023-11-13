import random
import chess
import time
from collections.abc import Iterator
from contextlib import contextmanager
import test_bot


@contextmanager
def game_manager() -> Iterator[None]:
    """Creates context for game."""

    print("===== GAME STARTED =====")
    ping: float = time.perf_counter()
    try:
        # DO NOT EDIT. This will be replaced w/ judging context manager.
        yield
    finally:
        pong: float = time.perf_counter()
        total = pong - ping
        print(f"Total game time = {total:.3f} seconds")
    print("===== GAME ENDED =====")


class Bot:
    def __init__(self, color, fen=None):
        self.board = chess.Board(fen if fen else "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        self.depth = 3
        self.color = color

    def check_move_is_legal(self, initial_position, new_position) -> bool:
        return chess.Move.from_uci(initial_position + new_position) in self.board.legal_moves

    def minimax(self, depth, alpha=float('-inf'), beta=float('inf'), maximizing_player=True):
        if depth == 0 or self.board.is_game_over():
            return self.evaluate_board(), None

        legal_moves = list(self.board.legal_moves)
        best_move = None

        if maximizing_player:
            best_eval = float('-inf')
            for move in legal_moves:
                self.board.push(move)
                evaluation, _ = self.minimax(depth - 1, alpha, beta, False)
                self.board.pop()

                if evaluation > best_eval:
                    best_eval = evaluation
                    best_move = move

                alpha = max(alpha, best_eval)
                if beta <= alpha:
                    break
        else:
            best_eval = float('inf')
            for move in legal_moves:
                self.board.push(move)
                evaluation, _ = self.minimax(depth - 1, alpha, beta, True)
                self.board.pop()

                if evaluation < best_eval:
                    best_eval = evaluation
                    best_move = move

                beta = min(beta, best_eval)
                if beta <= alpha:
                    break

        return best_eval, best_move

    def is_king_exposed(self, king_square):
        return not self.board.has_kingside_castling_rights(not self.color) and not self.board.has_queenside_castling_rights(
            not self.color
        )

    def get_attack_against_king_bonus(self):
        bonus = 0
        opponent_king_square = self.board.king(not self.color)
        if self.is_king_exposed(opponent_king_square):
            bonus += 10
        if opponent_king_square in [chess.D4, chess.E4, chess.D5, chess.E5]:
            bonus += 5
        return bonus

    def get_checkmate_threat_bonus(self):
        bonus = 0
        if self.board.is_checkmate():
            bonus += 50
        opponent_king_square = self.board.king(not self.color)
        escape_squares = self.board.attacks(opponent_king_square)
        if len(escape_squares) <= 2:
            bonus += 20
        return bonus

    def get_protect_key_pieces_bonus(self):
        bonus = 0
        my_queen_squares = self.board.pieces(chess.QUEEN, self.color)
        if my_queen_squares:
            my_queen_square = my_queen_squares.pop()
            attacks_on_queen = len(self.board.attackers(not self.color, my_queen_square))
            if attacks_on_queen == 0:
                bonus += 4

        opponent_queen_squares = self.board.pieces(chess.QUEEN, not self.color)
        if opponent_queen_squares:
            opponent_queen_square = opponent_queen_squares.pop()
            attacks_on_queen = len(self.board.attackers(self.color, opponent_queen_square))
            if attacks_on_queen == 0:
                bonus -= 2

        for square in self.board.pieces(chess.ROOK, self.color):
            attacks_on_rook = len(self.board.attackers(not self.color, square))
            if attacks_on_rook == 0:
                bonus += 2

        for square in self.board.pieces(chess.ROOK, not self.color):
            attacks_on_rook = len(self.board.attackers(self.color, square))
            if attacks_on_rook == 0:
                bonus -= 1

        for square in self.board.pieces(chess.KNIGHT, self.color):
            attacks_on_knight = len(self.board.attackers(not self.color, square))
            if attacks_on_knight == 0:
                bonus += 1

        for square in self.board.pieces(chess.BISHOP, self.color):
            attacks_on_bishop = len(self.board.attackers(not self.color, square))
            if attacks_on_bishop == 0:
                bonus += 1

        return bonus

    def evaluate_board(self):
        score = 0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)

            if piece is not None:
                if piece.color == self.color:
                    score += self.get_piece_value(piece, square)
                else:
                    score -= self.get_piece_value(piece, square)

        if self.board.king(self.color) is not None and self.board.king(not self.color) is not None:
            my_king_square = self.board.king(self.color)
            opponent_king_square = self.board.king(not self.color)

            score += self.get_king_safety_bonus(my_king_square)
            score += self.get_checkmate_threat_bonus()
            score += self.get_attack_against_king_bonus()
            score -= self.get_king_safety_penalty(opponent_king_square)
            score += self.get_protect_key_pieces_bonus()

        return score

    def get_piece_value(self, piece, square):
        value = 0
        if piece.symbol().lower() == 'p':
            value = 1
        elif piece.symbol().lower() == 'r':
            value = 5
        elif piece.symbol().lower() == 'n':
            value = 3
        elif piece.symbol().lower() == 'b':
            value = 3
        elif piece.symbol().lower() == 'q':
            value = 9
        elif piece.symbol().lower() == 'k':
            value = 100

        if piece.color == self.color:
            if square in [chess.D4, chess.E4, chess.D5, chess.E5]:
                value += 0.5
        else:
            if square in [chess.D4, chess.E4, chess.D5, chess.E5]:
                value -= 0.5

        return value

    def get_king_safety_bonus(self, king_square):
        bonus = 0
        if self.board.has_kingside_castling_rights(self.color) and king_square == chess.E1:
            bonus += 2

        if self.board.has_queenside_castling_rights(self.color) and king_square == chess.E1:
            bonus += 2

        return bonus

    def get_king_safety_penalty(self, king_square):
        penalty = 0
        if not self.board.has_kingside_castling_rights(not self.color) and king_square == chess.E8:
            penalty -= 2

        if not self.board.has_queenside_castling_rights(not self.color) and king_square == chess.E8:
            penalty -= 2

        return penalty

    def get_best_move(self):
        best_move = self.minimax(self.depth)
        return best_move

    def next_move(self) -> str:
        eval, move = self.minimax(self.depth)
        print("My move: " + str(move))
        return str(move)


if __name__ == "__main__":

    chess_bot = Bot(color=chess.WHITE)  # Specify the color (chess.WHITE or chess.BLACK)
    with game_manager():
        playing = True

        while playing:
            if chess_bot.color == chess.board.turn: # Checking whose turn it is
                chess_bot.board.push_san(chess_bot.next_move())
            else:
                chess_bot.board.push_san(test_bot.get_move(chess_bot.board))
            print(chess_bot.board, end="\n\n")

            if chess_bot.board.is_game_over():
                if chess_bot.board.is_stalemate():
                    print("Is stalemate")
                elif chess_bot.board.is_insufficient_material():
                    print("Is insufficient material")

                print(chess_bot.board.outcome())

                playing = False
