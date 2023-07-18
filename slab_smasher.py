import pygame
import numpy as np
from hand import hand_position, track_hand, current_frame, frame_lock, hand_position_queue, hand_position_updated
import threading
import cv2

pygame.init()

# settings
screen_width, screen_height = 640, 480
white = (255, 255, 255)     
black = (0, 0, 0)
brick_colors = [(0, 255, 0), (255, 255, 0), (255, 0, 0), (0,0,0)] 
paddle_width, paddle_height = 100, 20
brick_width, brick_height = screen_width // 10, 30 
brick_rows = 5 
paddle_speed = 10
ball_radius = 10
ball_speed = [15,-15]


win = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Slab Smasher")




def draw_paddle(x):
    pygame.draw.rect(win, white, (x, screen_height - paddle_height, paddle_width, paddle_height))


def draw_brick(x, y, hits):
    color = brick_colors[min(hits, len(brick_colors) - 1)]

    pygame.draw.rect(win, color, (x, y, brick_width, brick_height))


prev_hand_pos = 0
max_hand_pos = 1000


def display_frame():

    global current_frame

    while True:
        with frame_lock:
            if current_frame is not None:
                frame = current_frame.copy()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame) 
                frame = np.flipud(frame) 
                frame_surface = pygame.surfarray.make_surface(frame)
                frame_surface = pygame.transform.scale(frame_surface, (screen_width, screen_height))

                win.blit(frame_surface, (0, 0))
                pygame.display.update()
def game_loop():
    global prev_hand_pos
    brick_x, brick_y = 50, 50
    paddle_x = (screen_width - paddle_width) // 2  # initial pos at center

    bricks = [{'x': brick_x, 'y': brick_y, 'hits': 0} for _ in range(5)]
    ball_x, ball_y = screen_width // 2, screen_height // 2
    bricks = []
    for row in range(brick_rows):
        for col in range(10):
            brick_x = brick_width * col
            brick_y = brick_height * row
            bricks.append({'x': brick_x, 'y': brick_y, 'hits': 0})


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        hand_position_updated.wait()
        hand_position_updated.clear()
        with frame_lock:
            if not hand_position_queue.empty():
                curr_hand_pos = hand_position_queue.get()
            else:
                curr_hand_pos = 0
    
        #hand position controlling paddle position
        curr_hand_pos = (curr_hand_pos + prev_hand_pos) / 2
        hand_diff = curr_hand_pos - prev_hand_pos
        hand_diff *= -1
        paddle_x += hand_diff * 2.025
        paddle_x = max(0, min(screen_width - paddle_width, paddle_x))
       


        #ball movement
        ball_x += ball_speed[0]
        ball_y += ball_speed[1]

        # wall collision
        if ball_x <= 0 or ball_x >= screen_width:
            ball_speed[0] *= -1
        if ball_y <= 0:
            ball_speed[1] *= -1
        elif ball_y >= screen_height:
            #ball exits screen bottom end game
            pygame.quit()
            quit()

        #ball collision with paddle
        if ball_y >= screen_height - paddle_height - ball_radius and \
           paddle_x <= ball_x <= paddle_x + paddle_width:
            paddle_center_x = paddle_x + paddle_width / 2
            distance_from_center = ball_x - paddle_center_x

            
            scaling_factor = distance_from_center / (paddle_width / 2)

            #scaling ball speed
            ball_speed[0] = 15 * scaling_factor

            ball_speed[1] *= -1

        #ball collision with brick
        for brick in bricks:
            if brick['hits'] < len(brick_colors) and \
               brick['x'] <= ball_x <= brick['x'] + brick_width and \
               brick['y'] <= ball_y <= brick['y'] + brick_height + ball_radius:
                ball_speed[1] *= -1
                brick['hits'] += 1

        win.fill(black)
        draw_paddle(paddle_x)
        for brick in bricks:
            draw_brick(brick['x'], brick['y'], brick['hits'])

        pygame.draw.circle(win, white, (int(ball_x), int(ball_y)), ball_radius)
        pygame.display.update()
        pygame.time.delay(30)


def main():
    #start game
    hand_tracking_thread = threading.Thread(target=track_hand)
    hand_tracking_thread.daemon = True
    hand_tracking_thread.start()

    display_thread = threading.Thread(target=display_frame)
    display_thread.daemon = True
    display_thread.start()

    game_loop()


if __name__ == "__main__":
    main()
