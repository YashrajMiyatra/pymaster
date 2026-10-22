"""
Complete, playable Snake Game built with Python and Tkinter.
Controls: Arrow Keys or WASD to change direction. Space to Pause/Restart.
"""

import tkinter as tk
import random

CELL_SIZE = 20
GRID_WIDTH = 25
GRID_HEIGHT = 25
GAME_WIDTH = CELL_SIZE * GRID_WIDTH
GAME_HEIGHT = CELL_SIZE * GRID_HEIGHT
INITIAL_SPEED = 120  # milliseconds per tick


class SnakeGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Python Snake Master - Tkinter GUI")
        self.root.resizable(False, False)

        # Header for Score
        self.score = 0
        self.high_score = 0
        self.is_game_over = False
        self.is_paused = False

        self.score_label = tk.Label(
            self.root,
            text="Score: 0  |  High Score: 0  |  [P] Pause  [R] Restart",
            font=("Consolas", 12, "bold"),
            bg="#1e1e1e",
            fg="#00ffcc",
            pady=8,
        )
        self.score_label.pack(fill=tk.X)

        # Canvas
        self.canvas = tk.Canvas(
            self.root,
            width=GAME_WIDTH,
            height=GAME_HEIGHT,
            bg="#0d1117",
            highlightthickness=0,
        )
        self.canvas.pack()

        # Key bindings
        self.root.bind("<Up>", lambda e: self.change_direction("Up"))
        self.root.bind("<Down>", lambda e: self.change_direction("Down"))
        self.root.bind("<Left>", lambda e: self.change_direction("Left"))
        self.root.bind("<Right>", lambda e: self.change_direction("Right"))
        self.root.bind("<w>", lambda e: self.change_direction("Up"))
        self.root.bind("<s>", lambda e: self.change_direction("Down"))
        self.root.bind("<a>", lambda e: self.change_direction("Left"))
        self.root.bind("<d>", lambda e: self.change_direction("Right"))
        self.root.bind("<space>", lambda e: self.toggle_pause())
        self.root.bind("<r>", lambda e: self.reset_game())
        self.root.bind("<p>", lambda e: self.toggle_pause())

        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.speed = INITIAL_SPEED
        self.is_game_over = False
        self.is_paused = False
        self.direction = "Right"
        self.next_direction = "Right"

        # Initial Snake (3 blocks in the center)
        mid_x = GRID_WIDTH // 2
        mid_y = GRID_HEIGHT // 2
        self.snake = [
            (mid_x, mid_y),
            (mid_x - 1, mid_y),
            (mid_x - 2, mid_y),
        ]

        self.spawn_food()
        self.update_score_display()
        self.draw()
        self.game_loop()

    def spawn_food(self):
        while True:
            fx = random.randint(0, GRID_WIDTH - 1)
            fy = random.randint(0, GRID_HEIGHT - 1)
            if (fx, fy) not in self.snake:
                self.food = (fx, fy)
                break

    def change_direction(self, new_dir: str):
        opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
        if opposites.get(new_dir) != self.direction:
            self.next_direction = new_dir

    def toggle_pause(self):
        if self.is_game_over:
            self.reset_game()
            return
        self.is_paused = not self.is_paused
        if not self.is_paused:
            self.game_loop()
        else:
            self.canvas.create_text(
                GAME_WIDTH // 2,
                GAME_HEIGHT // 2,
                text="PAUSED",
                fill="#ffaa00",
                font=("Consolas", 24, "bold"),
                tags="pause_text",
            )

    def update_score_display(self):
        self.score_label.config(
            text=f"Score: {self.score}  |  High Score: {self.high_score}  |  [Space] Pause  [R] Restart"
        )

    def game_loop(self):
        if self.is_game_over or self.is_paused:
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]

        if self.direction == "Up":
            new_head = (head_x, head_y - 1)
        elif self.direction == "Down":
            new_head = (head_x, head_y + 1)
        elif self.direction == "Left":
            new_head = (head_x - 1, head_y)
        elif self.direction == "Right":
            new_head = (head_x + 1, head_y)

        # Collision with walls
        nx, ny = new_head
        if nx < 0 or nx >= GRID_WIDTH or ny < 0 or ny >= GRID_HEIGHT:
            self.game_over()
            return

        # Collision with self
        if new_head in self.snake:
            self.game_over()
            return

        # Move snake
        self.snake.insert(0, new_head)

        # Check food eaten
        if new_head == self.food:
            self.score += 10
            if self.score > self.high_score:
                self.high_score = self.score
            self.update_score_display()
            self.spawn_food()
            # Speed up slightly every 50 points
            if self.score % 50 == 0 and self.speed > 60:
                self.speed -= 8
        else:
            self.snake.pop()

        self.draw()
        self.root.after(self.speed, self.game_loop)

    def draw(self):
        self.canvas.delete("all")

        # Draw grid subtle dots
        for x in range(0, GAME_WIDTH, CELL_SIZE * 5):
            self.canvas.create_line(x, 0, x, GAME_HEIGHT, fill="#161b22", width=1)
        for y in range(0, GAME_HEIGHT, CELL_SIZE * 5):
            self.canvas.create_line(0, y, GAME_WIDTH, y, fill="#161b22", width=1)

        # Draw Food (Glow red circle)
        fx, fy = self.food
        x1 = fx * CELL_SIZE + 2
        y1 = fy * CELL_SIZE + 2
        x2 = (fx + 1) * CELL_SIZE - 2
        y2 = (fy + 1) * CELL_SIZE - 2
        self.canvas.create_oval(x1, y1, x2, y2, fill="#ff3366", outline="#ff6699", width=2)

        # Draw Snake
        for idx, (sx, sy) in enumerate(self.snake):
            px1 = sx * CELL_SIZE + 1
            py1 = sy * CELL_SIZE + 1
            px2 = (sx + 1) * CELL_SIZE - 1
            py2 = (sy + 1) * CELL_SIZE - 1

            if idx == 0:
                # Head: bright cyan
                self.canvas.create_rectangle(px1, py1, px2, py2, fill="#00ffcc", outline="#33ffff", width=2)
            else:
                # Body: emerald green gradient
                self.canvas.create_rectangle(px1, py1, px2, py2, fill="#00cc66", outline="#00994d", width=1)

    def game_over(self):
        self.is_game_over = True
        self.canvas.create_rectangle(
            40, GAME_HEIGHT // 2 - 60, GAME_WIDTH - 40, GAME_HEIGHT // 2 + 60,
            fill="#161b22", outline="#ff3366", width=3
        )
        self.canvas.create_text(
            GAME_WIDTH // 2,
            GAME_HEIGHT // 2 - 20,
            text="GAME OVER",
            fill="#ff3366",
            font=("Consolas", 26, "bold"),
        )
        self.canvas.create_text(
            GAME_WIDTH // 2,
            GAME_HEIGHT // 2 + 20,
            text=f"Final Score: {self.score}   |   Press [R] to Play Again",
            fill="#ffffff",
            font=("Consolas", 12),
        )


def main():
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
