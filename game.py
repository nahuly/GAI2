import streamlit as st
import pygame
import random

# Streamlit 인터페이스 설정
st.title("장애물 피하기 게임")
st.write("화살표 키를 사용하여 장애물을 피해보세요!")

# 게임 상태 변수
game_running = False
game_paused = False

# 버튼 설정
if st.button('시작'):
    game_running = True
    game_paused = False

if st.button('일시정지'):
    game_paused = True

if st.button('다시 시작'):
    game_paused = False

# pygame 초기화
pygame.init()

# 화면 크기 설정
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))

# 색상 정의
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)

# 플레이어 설정
player_size = 50
player_pos = [screen_width // 2, screen_height - 2 * player_size]

# 장애물 설정
obstacle_size = 50
obstacle_pos = [random.randint(0, screen_width - obstacle_size), 0]
obstacle_list = [obstacle_pos]
speed = 10

# 게임 속도 설정
clock = pygame.time.Clock()

# 폰트 설정
font = pygame.font.SysFont("monospace", 35)

# 점수 초기화
score = 0

# 장애물 생성 함수


def drop_obstacles(obstacle_list):
    delay = random.random()
    if len(obstacle_list) < 10 and delay < 0.1:
        x_pos = random.randint(0, screen_width - obstacle_size)
        y_pos = 0
        obstacle_list.append([x_pos, y_pos])

# 장애물 위치 업데이트 함수


def update_obstacle_positions(obstacle_list, score):
    for idx, obstacle_pos in enumerate(obstacle_list):
        if obstacle_pos[1] >= 0 and obstacle_pos[1] < screen_height:
            obstacle_pos[1] += speed
        else:
            obstacle_list.pop(idx)
            score += 1
    return score

# 충돌 감지 함수


def collision_check(obstacle_list, player_pos):
    for obstacle_pos in obstacle_list:
        if detect_collision(obstacle_pos, player_pos):
            return True
    return False

# 충돌 감지 보조 함수


def detect_collision(player_pos, obstacle_pos):
    p_x = player_pos[0]
    p_y = player_pos[1]

    o_x = obstacle_pos[0]
    o_y = obstacle_pos[1]

    if (o_x >= p_x and o_x < (p_x + player_size)) or (p_x >= o_x and p_x < (o_x + obstacle_size)):
        if (o_y >= p_y and o_y < (p_y + player_size)) or (p_y >= o_y and p_y < (o_y + obstacle_size)):
            return True
    return False


# 게임 루프
while game_running:

    if game_paused:
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False

        if event.type == pygame.KEYDOWN:
            x = player_pos[0]
            y = player_pos[1]
            if event.key == pygame.K_LEFT:
                x -= player_size
            elif event.key == pygame.K_RIGHT:
                x += player_size

            player_pos = [x, y]

    screen.fill(black)

    drop_obstacles(obstacle_list)
    score = update_obstacle_positions(obstacle_list, score)

    if collision_check(obstacle_list, player_pos):
        game_running = False
        break

    for obstacle_pos in obstacle_list:
        pygame.draw.rect(
            screen, red, (obstacle_pos[0], obstacle_pos[1], obstacle_size, obstacle_size))

    pygame.draw.rect(
        screen, white, (player_pos[0], player_pos[1], player_size, player_size))

    text = font.render("Score: {}".format(score), True, white)
    screen.blit(text, (10, 10))

    clock.tick(30)

    pygame.display.update()

pygame.quit()
st.write("게임 종료!")
st.write(f"최종 점수: {score}")
